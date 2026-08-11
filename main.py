from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.core.clipboard import Clipboard

# ==========================================
# CONFIGURACIÓN DE ABECEDARIOS Y CAPA 0
# ==========================================
ALFABETO_NORMAL = "ABCDEFGHIJKLMNOPQRSTUVWXY"
ALFABETO_ROHEN  = "FBAECGMTUPKWSXQRDHNILJOYV"

INDICE_CHAR = {char: idx for idx, char in enumerate(ALFABETO_ROHEN)}
CHAR_INDICE = {idx: char for idx, char in enumerate(ALFABETO_ROHEN)}
MOD = len(ALFABETO_ROHEN)

MAPEO_CAPA_0 = {ALFABETO_NORMAL[i]: ALFABETO_ROHEN[i] for i in range(25)}
MAPEO_INVERSO_CAPA_0 = {ALFABETO_ROHEN[i]: ALFABETO_NORMAL[i] for i in range(25)}

def aplicar_capa_0(texto):
    texto = texto.upper().replace('Z', 'Y').replace('Ñ', 'N')
    return "".join([MAPEO_CAPA_0[c] for c in texto if c in MAPEO_CAPA_0])

def revertir_capa_0(texto):
    texto = texto.upper()
    return "".join([MAPEO_INVERSO_CAPA_0[c] for c in texto if c in MAPEO_INVERSO_CAPA_0])

# ==========================================
# VIGENÈRE AUTOKEY
# ==========================================
def autokey_vigenere_encrypt(texto, clave_base):
    texto = "".join([c for c in texto.upper() if c in INDICE_CHAR])
    clave_base = clave_base.upper()
    clave_completa = list(clave_base)
    for i in range(len(texto) - len(clave_base)):
        clave_completa.append(texto[i])
    clave_completa = "".join(clave_completa[:len(texto)])
    
    resultado = []
    for i, char in enumerate(texto):
        c_idx = INDICE_CHAR[char]
        k_idx = INDICE_CHAR[clave_completa[i]]
        resultado.append(CHAR_INDICE[(c_idx + k_idx) % MOD])
    return "".join(resultado)

def autokey_vigenere_decrypt(texto_cifrado, clave_base):
    texto_cifrado = "".join([c for c in texto_cifrado.upper() if c in INDICE_CHAR])
    clave_base = clave_base.upper()
    texto_plano = []
    for i, char in enumerate(texto_cifrado):
        k_char = clave_base[i] if i < len(clave_base) else texto_plano[i - len(clave_base)]
        c_idx = INDICE_CHAR[char]
        k_idx = INDICE_CHAR[k_char]
        texto_plano.append(CHAR_INDICE[(c_idx - k_idx) % MOD])
    return "".join(texto_plano)

def triple_autokey_encrypt(texto, k1, k2, k3):
    p1 = autokey_vigenere_encrypt(texto, k1)
    p2 = autokey_vigenere_encrypt(p1, k2)
    return autokey_vigenere_encrypt(p2, k3)

def triple_autokey_decrypt(texto_cifrado, k1, k2, k3):
    p1 = autokey_vigenere_decrypt(texto_cifrado, k3)
    p2 = autokey_vigenere_decrypt(p1, k2)
    return autokey_vigenere_decrypt(p2, k1)

# ==========================================
# TRANSPOSICIÓN COLUMNAR
# ==========================================
def _obtener_orden_columnas(clave):
    return [i for i, _ in sorted(enumerate(clave), key=lambda x: x[1])]

def encriptar_transposicion(texto, clave, relleno="X"):
    num_cols = len(clave)
    num_filas = -(-len(texto) // num_cols)
    texto_padded = texto.ljust(num_filas * num_cols, relleno)
    grid = [texto_padded[i * num_cols : (i + 1) * num_cols] for i in range(num_filas)]
    orden = _obtener_orden_columnas(clave)
    cifrado = []
    for col in orden:
        for fila in range(num_filas):
            cifrado.append(grid[fila][col])
    return "".join(cifrado)

def desencriptar_transposicion(texto_cifrado, clave):
    num_cols = len(clave)
    num_filas = len(texto_cifrado) // num_cols
    orden = _obtener_orden_columnas(clave)
    grid = [[""] * num_cols for _ in range(num_filas)]
    idx = 0
    for col in orden:
        for fila in range(num_filas):
            grid[fila][col] = texto_cifrado[idx]
            idx += 1
    return "".join(["".join(fila) for fila in grid])

# ==========================================
# FLUJOS COMPLETOS (MARÍA 3)
# ==========================================
def encriptar_capa_simple(texto, kv1, kv2, kv3, kt):
    texto_limpio = "".join([c for c in texto.upper() if c in INDICE_CHAR])
    vigenere_out = triple_autokey_encrypt(texto_limpio, kv1, kv2, kv3)
    return encriptar_transposicion(vigenere_out, kt)

def desencriptar_capa_simple(texto_cifrado, kv1, kv2, kv3, kt):
    transposicion_out = desencriptar_transposicion(texto_cifrado, kt)
    return triple_autokey_decrypt(transposicion_out, kv1, kv2, kv3)

def encriptar_doble_absoluto(texto, k1, k2, k3, kt1, k4, k5, k6, kt2):
    mutado = aplicar_capa_0(texto)
    fase_1 = encriptar_capa_simple(mutado, k1, k2, k3, kt1)
    return encriptar_capa_simple(fase_1, k4, k5, k6, kt2)

def desencriptar_doble_absoluto(texto_cifrado, k1, k2, k3, kt1, k4, k5, k6, kt2):
    fase_1 = desencriptar_capa_simple(texto_cifrado, k4, k5, k6, kt2)
    crudo = desencriptar_capa_simple(fase_1, k1, k2, k3, kt1)
    return revertir_capa_0(crudo)

# ==========================================
# INTERFAZ GRÁFICA KIVY (AMPLIADA)
# ==========================================
class RohenApp(App):
    def build(self):
        root = ScrollView(size_hint=(1, 1))
        layout = BoxLayout(orientation='vertical', padding=15, spacing=12, size_hint_y=None)
        layout.bind(minimum_height=layout.setter('height'))

        layout.add_widget(Label(text='LAS TRES MARÍAS - ROHEN', font_size=22, bold=True, size_hint_y=None, height=45))

        # Caja de mensaje grande y multilínea
        layout.add_widget(Label(text='Mensaje o Criptograma:', size_hint_y=None, height=25))
        self.txt_mensaje = TextInput(
            text='', 
            hint_text='Escribe o pega tu mensaje aquí...', 
            size_hint_y=None, 
            height=120, 
            multiline=True
        )
        layout.add_widget(self.txt_mensaje)

        layout.add_widget(Label(text='Claves Capa 1 (V1, V2, V3, Transp 1):', size_hint_y=None, height=25))
        self.k1 = TextInput(text='rohen', size_hint_y=None, height=40, multiline=False)
        self.k2 = TextInput(text='rohenebri', size_hint_y=None, height=40, multiline=False)
        self.k3 = TextInput(text='britons', size_hint_y=None, height=40, multiline=False)
        self.kt1 = TextInput(text='rohenebrit', size_hint_y=None, height=40, multiline=False)
        
        for w in [self.k1, self.k2, self.k3, self.kt1]:
            layout.add_widget(w)

        layout.add_widget(Label(text='Claves Capa 2 (V4, V5, V6, Transp 2):', size_hint_y=None, height=25))
        self.k4 = TextInput(text='rohenebri', size_hint_y=None, height=40, multiline=False)
        self.k5 = TextInput(text='rohen', size_hint_y=None, height=40, multiline=False)
        self.k6 = TextInput(text='britons', size_hint_y=None, height=40, multiline=False)
        self.kt2 = TextInput(text='rohenebrit', size_hint_y=None, height=40, multiline=False)

        for w in [self.k4, self.k5, self.k6, self.kt2]:
            layout.add_widget(w)

        btn_layout = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=None, height=55)
        btn_enc = Button(text='Encriptar', bold=True)
        btn_enc.bind(on_press=self.ejecutar_encriptar)
        btn_dec = Button(text='Desencriptar', bold=True)
        btn_dec.bind(on_press=self.ejecutar_desencriptar)
        
        btn_layout.add_widget(btn_enc)
        btn_layout.add_widget(btn_dec)
        layout.add_widget(btn_layout)

        # Caja de resultado grande y multilínea
        layout.add_widget(Label(text='Resultado:', size_hint_y=None, height=25))
        self.txt_resultado = TextInput(
            text='', 
            readonly=True, 
            size_hint_y=None, 
            height=140, 
            multiline=True
        )
        layout.add_widget(self.txt_resultado)

        btn_copiar = Button(text='Copiar Resultado', size_hint_y=None, height=50)
        btn_copiar.bind(on_press=self.copiar_texto)
        layout.add_widget(btn_copiar)

        root.add_widget(layout)
        return root

    def ejecutar_encriptar(self, instance):
        try:
            res = encriptar_doble_absoluto(
                self.txt_mensaje.text,
                self.k1.text, self.k2.text, self.k3.text, self.kt1.text,
                self.k4.text, self.k5.text, self.k6.text, self.kt2.text
            )
            self.txt_resultado.text = res
        except Exception as e:
            self.txt_resultado.text = f"Error: {e}"

    def ejecutar_desencriptar(self, instance):
        try:
            res = desencriptar_doble_absoluto(
                self.txt_mensaje.text,
                self.k1.text, self.k2.text, self.k3.text, self.kt1.text,
                self.k4.text, self.k5.text, self.k6.text, self.kt2.text
            )
            self.txt_resultado.text = res
        except Exception as e:
            self.txt_resultado.text = f"Error: {e}"

    def copiar_texto(self, instance):
        if self.txt_resultado.text:
            Clipboard.copy(self.txt_resultado.text)

if __name__ == '__main__':
    RohenApp().run()
