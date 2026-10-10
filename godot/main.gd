extends Control
# SpellSpeak basic UI. The whole UI is built in code, so main.tscn stays tiny.
# Game loop: pick spell -> press Cast -> partial text -> endpoint -> score -> HP.
# The backend sends "mock": true while it is in mock mode; the banner shows it.

const URL := "ws://127.0.0.1:8765"
const WORDS := ["think", "very", "three", "this"]  # placeholder spells, replace later
const MONSTER_HP := 100
const MAX_ERRORS_FOR_HIT := 1  # PLACEHOLDER. Calibrate from your own data, do not guess.

var ws := WebSocketPeer.new()
var connected := false
var word_index := 0
var monster_hp := MONSTER_HP

var banner: Label
var status: Label
var target_label: Label
var partial_label: Label
var feedback: RichTextLabel
var hp_bar: ProgressBar
var cast_btn: Button
var next_btn: Button


func _ready() -> void:
	var box := VBoxContainer.new()
	box.set_anchors_preset(Control.PRESET_FULL_RECT)
	box.add_theme_constant_override("separation", 12)
	add_child(box)

	banner = _label(box, "", 16)
	status = _label(box, "Connecting...", 16)
	target_label = _label(box, "", 40)
	partial_label = _label(box, "Heard: ", 24)
	hp_bar = ProgressBar.new()
	hp_bar.max_value = MONSTER_HP
	hp_bar.value = monster_hp
	hp_bar.custom_minimum_size = Vector2(0, 28)
	box.add_child(hp_bar)
	feedback = RichTextLabel.new()
	feedback.bbcode_enabled = true
	feedback.fit_content = true
	feedback.custom_minimum_size = Vector2(0, 120)
	box.add_child(feedback)
	cast_btn = Button.new()
	cast_btn.text = "Cast spell"
	cast_btn.pressed.connect(_on_cast)
	box.add_child(cast_btn)
	next_btn = Button.new()
	next_btn.text = "Next spell"
	next_btn.pressed.connect(_on_next)
	box.add_child(next_btn)

	_show_word()
	ws.connect_to_url(URL)


func _label(parent: Node, text: String, size: int) -> Label:
	var l := Label.new()
	l.text = text
	l.add_theme_font_size_override("font_size", size)
	parent.add_child(l)
	return l


func _show_word() -> void:
	target_label.text = WORDS[word_index]
	partial_label.text = "Heard: "
	feedback.text = ""


func _on_next() -> void:
	word_index = (word_index + 1) % WORDS.size()
	_show_word()


func _on_cast() -> void:
	if not connected:
		status.text = "Not connected. Start backend/server.py first."
		return
	partial_label.text = "Heard: "
	feedback.text = ""
	status.text = "Listening..."
	ws.send_text(JSON.stringify({"type": "start", "word": WORDS[word_index]}))


func _process(_delta: float) -> void:
	ws.poll()
	var state := ws.get_ready_state()
	if state == WebSocketPeer.STATE_OPEN:
		if not connected:
			connected = true
			status.text = "Connected."
		while ws.get_available_packet_count() > 0:
			_handle(ws.get_packet().get_string_from_utf8())
	elif state == WebSocketPeer.STATE_CLOSED and connected:
		connected = false
		status.text = "Disconnected."


func _handle(raw: String) -> void:
	var msg = JSON.parse_string(raw)
	if typeof(msg) != TYPE_DICTIONARY:
		return
	if msg.get("mock", false):
		banner.text = "MOCK MODE: values below are NOT real measurements"
	match msg.get("type", ""):
		"partial":
			partial_label.text = "Heard: " + str(msg.get("text", ""))
		"endpoint":
			status.text = "Scoring..."
		"score":
			_show_score(msg)
		"error":
			status.text = "Error: " + str(msg.get("detail", ""))


func _show_score(msg: Dictionary) -> void:
	status.text = "PER %.2f (S%d D%d I%d of %d phonemes)" % [
		msg.get("per", 0.0), msg.get("S", 0), msg.get("D", 0), msg.get("I", 0), msg.get("N", 0)]
	var lines := ""
	for e in msg.get("errors", []):
		match e.get("op", ""):
			"sub": lines += "[color=orange]/%s/ heard as /%s/[/color]\n" % [e["ref"], e["heard"]]
			"del": lines += "[color=red]/%s/ missing[/color]\n" % e["ref"]
			"ins": lines += "[color=red]extra /%s/[/color]\n" % e["heard"]
	if lines == "":
		lines = "[color=green]All phonemes match.[/color]"
	feedback.text = lines
	var errors := int(msg.get("S", 0)) + int(msg.get("D", 0)) + int(msg.get("I", 0))
	if errors <= MAX_ERRORS_FOR_HIT:
		monster_hp = max(0, monster_hp - 25)
		hp_bar.value = monster_hp
		if monster_hp == 0:
			status.text += "  |  Monster defeated!"
			monster_hp = MONSTER_HP
			hp_bar.value = monster_hp
