# will test and eventually change to qmk later when the board comes
import board
import busio

from kmk.kmk_keyboard import KMKKeyboard
from kmk.keys import KC
from kmk.scanners import DiodeOrientation
from kmk.scanners.keypad import MatrixScanner
from kmk.modules.encoder import EncoderHandler
from kmk.extensions.media_keys import MediaKeys
from kmk.extensions.RGB import RGB, AnimationModes
from kmk.extensions.peg_oled_display import Oled, OledDisplayMode, OledReactionType, OledData

# -------------------------------------------------------------------------
# CUSTOM SCANNER FOR JAPANESE DUPLEX
# -------------------------------------------------------------------------
class JapaneseDuplexScanner:
    def __init__(self, col_pins, row_pins):
        self.scanner_fwd = MatrixScanner(
            cols=col_pins, 
            rows=row_pins, 
            diode_orientation=DiodeOrientation.COL2ROW
        )
        self.scanner_rev = MatrixScanner(
            cols=row_pins, 
            rows=col_pins, 
            diode_orientation=DiodeOrientation.COL2ROW
        )
        self.offset = len(col_pins) * len(row_pins)

    @property
    def key_count(self):
        return self.scanner_fwd.key_count + self.scanner_rev.key_count

    def scan_for_changes(self):
        events = self.scanner_fwd.scan_for_changes()
        rev_events = self.scanner_rev.scan_for_changes()
        for event in rev_events:
            event.key_number += self.offset
            events.append(event)
        return events

# -------------------------------------------------------------------------
# PIN DEFINITIONS (Seeed Xiao RP2040)
# -------------------------------------------------------------------------
keyboard = KMKKeyboard()

# 1. MATRIX (6 Pins)
# We use D0, D1 for Cols and D2, D3, D6, D7 for Rows.
# We SKIP D4/D5 because they are the default I2C pins for the OLED.
col_pins = (board.D0, board.D1)
row_pins = (board.D2, board.D3, board.D6, board.D7)

keyboard.matrix = JapaneseDuplexScanner(col_pins=col_pins, row_pins=row_pins)

# Coord Mapping: 2 cols * 4 rows = 8 forward + 8 reverse = 16 keys
# This mapping assumes you paired the keys physically (Key1+Key2, Key3+Key4...)
keyboard.coord_mapping = [
    0,  8,  1,  9,  
    2, 10,  3, 11,   
    4, 12,  5, 13,   
    6, 14,  7, 15    
]

# -------------------------------------------------------------------------
# 2. ENCODER (2 Pins)
# -------------------------------------------------------------------------
# Using D8 and D9. 
# WARNING: No pin left for the Encoder 'Click' switch. 
# You only get rotation unless you wire the click into the matrix as a 17th key.
layers_ext = keyboard.modules.append(EncoderHandler())
encoder_handler = EncoderHandler()
keyboard.modules.append(encoder_handler)

encoder_handler.pins = ((board.D8, board.D9, None),) 
encoder_handler.map = [((KC.VOLD, KC.VOLU, KC.MUTE),),]

# -------------------------------------------------------------------------
# 3. PER-KEY RGB (1 Pin)
# -------------------------------------------------------------------------
# Using D10. This is the last remaining pin.
rgb = RGB(
    pixel_pin=board.D10,
    num_pixels=16,
    val_limit=100,
    hue_default=10,
    sat_default=255,
    val_default=100,
    animation_mode=AnimationModes.RAINBOW
)
keyboard.extensions.append(rgb)

# -------------------------------------------------------------------------
# 4. OLED DISPLAY (2 Pins)
# -------------------------------------------------------------------------
# Using D4 (SDA) and D5 (SCL) - These are the hardware I2C pins on Xiao
i2c_bus = busio.I2C(board.D5, board.D4) # (SCL, SDA)

oled_ext = Oled(
    OledData(
        corner_one={0:OledReactionType.STATIC, 1:["Layer"]},
        corner_two={0:OledReactionType.LAYER, 1:["0", "1"]},
        corner_three={0:OledReactionType.STATIC, 1:["KMK"]},
        corner_four={0:OledReactionType.STATIC, 1:["Pad"]},
    ),
    toDisplay=OledDisplayMode.TXT,
    flip=False,
)
keyboard.extensions.append(oled_ext)

# -------------------------------------------------------------------------
# 5. KEYMAP
# -------------------------------------------------------------------------
keyboard.extensions.append(MediaKeys())

keyboard.keymap = [
    [
        KC.N7,    KC.N8,   KC.N9,   KC.BSPC,
        KC.N4,    KC.N5,   KC.N6,   KC.TAB,
        KC.N1,    KC.N2,   KC.N3,   KC.ENTER,
        KC.N0,    KC.DOT,  KC.A,    KC.MO(1),
    ],
    [
        KC.TRNS,  KC.TRNS, KC.TRNS, KC.TRNS,
        KC.RGB_TOG, KC.RGB_HUI, KC.RGB_SAI, KC.RGB_VAI,
        KC.RGB_M_P, KC.RGB_HUD, KC.RGB_SAD, KC.RGB_VAD,
        KC.TRNS,  KC.TRNS, KC.TRNS, KC.TRNS,
    ]
]

if __name__ == '__main__':
    keyboard.go()
