extends Control
# SpellSpeak — wizard-themed pronunciation trainer
# MOCK MODE active until backend/server.py uses real mic + models.
# DO NOT use any values from mock runs in your report.

const URL := "ws://127.0.0.1:8765"
const WORDS := ["think", "very", "three", "this", "father", "cloth", "breathe", "thirty"]
const MONSTER_HP := 100
const MAX_ERRORS_FOR_HIT := 1  # PLACEHOLDER — calibrate from your own PER data

const TIER_LABEL := ["Apprentice", "Adept", "Archmage"]
const MONSTER_SPRITES := ["👾", "🐉", "💀", "🧟", "🦇"]

const IPA_HINT := {
	"think": "/θɪŋk/",
	"very": "/ˈvɛri/",
	"three": "/θriː/",
	"this": "/ðɪs/",
	"father": "/ˈfɑːðə/",
	"cloth": "/klɒθ/",
	"breathe": "/briːð/",
	"thirty": "/ˈθɜːti/",
}

var ws := WebSocketPeer.new()
var connected := false
var word_index := 0
var monster_hp := MONSTER_HP
var is_mock := false

enum S { IDLE, LISTENING, SCORING }
var state := S.IDLE
var t_cast := 0
var t_first := 0
var t_end := 0

var banner: Label
var status: Label
var tier_label: Label
var monster_label: Label
var hp_bar: ProgressBar
var target_label: Label
var ipa_label: Label
var partial_label: Label
var feedback: RichTextLabel
var cast_btn: Button
var next_btn: Button


func _ready() -> void:
	# Background
	var bg := ColorRect.new()
	bg.color = Color(0.07, 0.04, 0.12)
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(bg)

	# Outer margin
	var margin := MarginContainer.new()
	margin.set_anchors_preset(Control.PRESET_FULL_RECT)
	margin.add_theme_constant_override("margin_left", 32)
	margin.add_theme_constant_override("margin_right", 32)
	margin.add_theme_constant_override("margin_top", 12)
	margin.add_theme_constant_override("margin_bottom", 12)
	add_child(margin)

	# Outer VBox: top area (expands) + button row (fixed)
	var outer := VBoxContainer.new()
	outer.add_theme_constant_override("separation", 0)
	margin.add_child(outer)

	# ── TOP SECTION (expands to fill) ──
	var top := VBoxContainer.new()
	top.size_flags_vertical = Control.SIZE_EXPAND_FILL
	top.add_theme_constant_override("separation", 6)
	outer.add_child(top)

	banner = _lbl(top, "", 12, Color(1.0, 0.85, 0.0))

	var row1 := HBoxContainer.new()
	top.add_child(row1)
	status = _lbl(row1, "Connecting...", 13, Color(0.6, 0.6, 0.6))
	status.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	tier_label = _lbl(row1, "Tier: Apprentice", 12, Color(0.5, 0.8, 1.0))

	top.add_child(_sep())

	# Monster row: emoji left, HP bar right
	var monster_row := HBoxContainer.new()
	monster_row.add_theme_constant_override("separation", 12)
	top.add_child(monster_row)
	monster_label = _lbl(monster_row, "👾", 40, Color.WHITE)
	var hp_col := VBoxContainer.new()
	hp_col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	hp_col.add_theme_constant_override("separation", 4)
	monster_row.add_child(hp_col)
	_lbl(hp_col, "Monster HP", 12, Color(0.8, 0.3, 0.3))
	hp_bar = ProgressBar.new()
	hp_bar.max_value = MONSTER_HP
	hp_bar.value = monster_hp
	hp_bar.custom_minimum_size = Vector2(0, 20)
	hp_bar.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	hp_bar.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	hp_col.add_child(hp_bar)

	top.add_child(_sep())

	var spell_hdr := _lbl(top, "✨  CAST YOUR SPELL  ✨", 12, Color(0.7, 0.5, 1.0))
	spell_hdr.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER

	target_label = _lbl(top, "", 46, Color(1.0, 1.0, 0.7))
	target_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	target_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL

	ipa_label = _lbl(top, "", 16, Color(0.6, 0.9, 0.6))
	ipa_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER

	partial_label = _lbl(top, "Heard: —", 18, Color(0.8, 0.8, 0.8))
	partial_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER

	feedback = RichTextLabel.new()
	feedback.bbcode_enabled = true
	feedback.fit_content = true
	feedback.size_flags_vertical = Control.SIZE_EXPAND_FILL
	feedback.add_theme_color_override("default_color", Color.WHITE)
	feedback.add_theme_font_size_override("normal_font_size", 15)
	top.add_child(feedback)

	# ── BUTTON ROW (always visible at bottom) ──
	top.add_child(_sep())
	var btn_row := HBoxContainer.new()
	btn_row.add_theme_constant_override("separation", 12)
	btn_row.size_flags_vertical = Control.SIZE_SHRINK_END
	outer.add_child(btn_row)

	cast_btn = Button.new()
	cast_btn.text = "🔮  Cast Spell"
	cast_btn.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	cast_btn.custom_minimum_size = Vector2(0, 40)
	cast_btn.pressed.connect(_on_cast)
	btn_row.add_child(cast_btn)

	next_btn = Button.new()
	next_btn.text = "⏭  Next Spell"
	next_btn.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	next_btn.custom_minimum_size = Vector2(0, 40)
	next_btn.pressed.connect(_on_next)
	btn_row.add_child(next_btn)

	_show_word()
	ws.connect_to_url(URL)


func _lbl(parent: Node, text: String, size: int, color: Color) -> Label:
	var l := Label.new()
	l.text = text
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", color)
	parent.add_child(l)
	return l


func _sep() -> HSeparator:
	return HSeparator.new()


func _show_word() -> void:
	monster_label.text = MONSTER_SPRITES[word_index % MONSTER_SPRITES.size()]
	target_label.text = WORDS[word_index]
	ipa_label.text = IPA_HINT.get(WORDS[word_index], "")
	partial_label.text = "Heard: —"
	feedback.text = ""
	tier_label.text = "Tier: " + TIER_LABEL[word_index % TIER_LABEL.size()]


func _on_next() -> void:
	if state != S.IDLE:
		return
	word_index = (word_index + 1) % WORDS.size()
	_show_word()


func _on_cast() -> void:
	if not connected:
		status.text = "Not connected — run backend/server.py first"
		return
	partial_label.text = "Heard: —"
	feedback.text = ""
	t_cast = Time.get_ticks_msec()
	t_first = 0
	t_end = 0
	_set_state(S.LISTENING)
	ws.send_text(JSON.stringify({"type": "start", "word": WORDS[word_index]}))


func _set_state(s: S) -> void:
	state = s
	match s:
		S.IDLE:
			status.text = "Ready."
			cast_btn.disabled = false
			next_btn.disabled = false
		S.LISTENING:
			status.text = "🎙  Listening..."
			cast_btn.disabled = true
			next_btn.disabled = true
		S.SCORING:
			status.text = "⚙  Scoring..."
			cast_btn.disabled = true
			next_btn.disabled = true


func _process(_delta: float) -> void:
	ws.poll()
	var s := ws.get_ready_state()
	if s == WebSocketPeer.STATE_OPEN:
		if not connected:
			connected = true
			_set_state(S.IDLE)
		while ws.get_available_packet_count() > 0:
			_handle(ws.get_packet().get_string_from_utf8())
	elif s == WebSocketPeer.STATE_CLOSED and connected:
		connected = false
		_set_state(S.IDLE)
		status.text = "Disconnected — restart backend/server.py"


func _handle(raw: String) -> void:
	var msg = JSON.parse_string(raw)
	if typeof(msg) != TYPE_DICTIONARY:
		return

	if msg.get("mock", false):
		is_mock = true
		banner.text = "⚠ MOCK MODE — values below are NOT real measurements"
	else:
		is_mock = false
		banner.text = ""

	if msg.has("ref_ipa"):
		ipa_label.text = msg["ref_ipa"]

	match msg.get("type", ""):
		"partial":
			if t_first == 0:
				t_first = Time.get_ticks_msec()
			partial_label.text = "Heard: " + str(msg.get("text", ""))
		"endpoint":
			t_end = Time.get_ticks_msec()
			_set_state(S.SCORING)
		"score":
			_show_score(msg)
			_log_attempt(msg, Time.get_ticks_msec())
			_set_state(S.IDLE)
		"error":
			status.text = "Error: " + str(msg.get("detail", ""))
			_set_state(S.IDLE)


func _show_score(msg: Dictionary) -> void:
	var per: float = msg.get("per", 0.0)
	var S_: int = msg.get("S", 0)
	var D: int = msg.get("D", 0)
	var I: int = msg.get("I", 0)
	var N: int = msg.get("N", 0)
	var errors := S_ + D + I
	var hit := errors <= MAX_ERRORS_FOR_HIT

	if hit:
		status.text = "✅ Spell cast!  PER %.2f  (S%d D%d I%d / %d)" % [per, S_, D, I, N]
		monster_hp = max(0, monster_hp - 25)
		hp_bar.value = monster_hp
		if monster_hp == 0:
			feedback.text = "[center][color=gold]⚔ Monster defeated! ⚔[/color][/center]"
			monster_label.text = "💥"
			monster_hp = MONSTER_HP
			hp_bar.value = monster_hp
			return
	else:
		status.text = "❌ Spell fizzled  PER %.2f  (S%d D%d I%d / %d)" % [per, S_, D, I, N]

	var lines := ""
	for e in msg.get("errors", []):
		match e.get("op", ""):
			"sub": lines += "[color=orange]  /%s/ → heard as /%s/[/color]\n" % [e["ref"], e["heard"]]
			"del": lines += "[color=red]  /%s/ missing[/color]\n" % e["ref"]
			"ins": lines += "[color=red]  extra /%s/[/color]\n" % e["heard"]
	if lines == "":
		lines = "[color=lime]  All phonemes match![/color]"
	feedback.text = lines


const LOG_PATH := "user://attempts.csv"

func _log_attempt(msg: Dictionary, t_score: int) -> void:
	var first_ms := (t_first - t_cast) if t_first > 0 else -1
	var endpoint_ms := (t_end - t_cast) if t_end > 0 else -1
	var score_ms := t_score - t_end

	var is_new := not FileAccess.file_exists(LOG_PATH)
	var f := FileAccess.open(LOG_PATH, FileAccess.WRITE if is_new else FileAccess.READ_WRITE)
	if f == null:
		return
	f.seek_end()
	if is_new:
		f.store_line("ts,word,mock,per,S,D,I,N,first_partial_ms,endpoint_ms,score_after_endpoint_ms")
	f.store_line("%s,%s,%s,%.4f,%d,%d,%d,%d,%d,%d,%d" % [
		Time.get_datetime_string_from_system(),
		WORDS[word_index], str(is_mock),
		msg.get("per", 0.0), msg.get("S", 0), msg.get("D", 0),
		msg.get("I", 0), msg.get("N", 0),
		first_ms, endpoint_ms, score_ms
	])
	f.close()
