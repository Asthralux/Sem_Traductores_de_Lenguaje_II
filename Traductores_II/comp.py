import pandas as pd
import re

class Pila:
    """Implementa una pila utilizando nodos enlazados."""

    class Nodo:
        """Nodo individual de la pila."""
        def __init__(self, valor, siguiente=None):
            self.valor = valor
            self.siguiente = siguiente

    def __init__(self):
        self.tope = None

    def push(self, valor):
        """Agrega un elemento a la cima de la pila.

        Parámetros:
            valor: El valor a agregar en la pila.
        """
        nuevo_nodo = self.Nodo(valor, self.tope)
        self.tope = nuevo_nodo

    def pop(self):
        """Elimina y retorna el elemento en la cima de la pila.

        Retorna:
            El valor que estaba en la cima de la pila.

        Excepciones:
            Exception: Si la pila está vacía.
        """
        if self.tope is None:
            raise Exception("Pila vacía")
        valor = self.tope.valor
        self.tope = self.tope.siguiente
        return valor

    def peek(self):
        """Retorna el elemento en la cima sin eliminarlo.

        Retorna:
            El valor en la cima de la pila.

        Excepciones:
            Exception: Si la pila está vacía.
        """
        if self.tope is None:
            raise Exception("Pila vacía")
        return self.tope.valor

    def esta_vacia(self):
        """Verifica si la pila está vacía.

        Retorna:
            bool: True si la pila está vacía, False en caso contrario.
        """
        return self.tope is None

    def mostrar(self):
        """Retorna una lista con los elementos de la pila desde la base hasta la cima.

        Retorna:
            list: Lista de elementos en la pila.

        Utilizado por:
            obtener_pila_como_cadena()
        """
        contenido = []
        nodo_actual = self.tope
        while nodo_actual is not None:
            contenido.append(nodo_actual.valor)
            nodo_actual = nodo_actual.siguiente
        return contenido[::-1]  # Invertir para mostrar desde la base hasta la cima

class Arbol:
    """Representa un nodo en el árbol de derivación sintáctica."""

    def __init__(self, valor):
        self.valor = valor
        self.hijos = []

    def __str__(self):
        return str(self.valor)

class AnalizadorLR:
    """Analizador sintáctico LR para realizar el análisis sintáctico de un lenguaje."""

    def __init__(self, archivo_tokens, archivo_tabla):
        self.simbolos = self.cargar_tokens(archivo_tokens)
        self.tabla = self.cargar_tabla(archivo_tabla)
        self.pila = Pila()
        self.pila.push(0)  # Estado inicial
        self.flujo_entrada = []
        self.errores_lexicos = []
        self.salida_proceso = []
        self.error_ocurrido = False
        self.arbol = None  # Nodo raíz del árbol de derivación

    def cargar_tokens(self, ruta_archivo):
        """Carga los tokens y sus identificadores numéricos desde un archivo.

        Parámetros:
            ruta_archivo (str): Ruta al archivo que contiene los tokens.

        Retorna:
            dict: Diccionario con los tokens y sus valores asociados.

        Llamado por:
            __init__()
        """
        simbolos = {}
        with open(ruta_archivo, 'r') as archivo:
            for linea in archivo:
                if '\t' in linea:
                    token, valor = linea.strip().split('\t')
                    simbolos[valor] = token
        return simbolos

    def cargar_tabla(self, ruta_archivo):
        """Carga la tabla LR desde un archivo CSV.

        Parámetros:
            ruta_archivo (str): Ruta al archivo CSV que contiene la tabla LR.

        Retorna:
            pandas.DataFrame: La tabla LR.

        Llamado por:
            __init__()
        """
        tabla = pd.read_csv(ruta_archivo, index_col=0)
        tabla.index = tabla.index.astype(int)
        tabla.columns = tabla.columns.str.strip()
        return tabla

    def analizar(self):
        """Realiza el análisis sintáctico utilizando la tabla LR.

        Este método es el núcleo del analizador. En cada iteración, obtiene la acción desde la tabla LR,
        realiza la acción correspondiente (desplazar, reducir, aceptar o manejar error) y actualiza la pila.

        Llama a:
            obtener_estado_actual()
            obtener_accion()
            desplazar()
            reducir()
            manejar_error()
            generar_salida()

        Utilizado por:
            Código principal al instanciar y llamar a analizar()
        """
        while True:
            if self.error_ocurrido:
                self.generar_salida()
                return

            estado_actual = self.obtener_estado_actual()
            token_actual = self.flujo_entrada[0] if self.flujo_entrada else '$'
            accion = self.obtener_accion(estado_actual, token_actual)

            pila_str = self.obtener_pila_como_cadena()
            entrada_str = ' '.join(self.flujo_entrada)
            self.salida_proceso.append((pila_str, entrada_str, accion))

            print(f"Pila actual: [ {pila_str} ]")

            if accion.startswith('d'):
                self.desplazar(accion, token_actual)
            elif accion.startswith('r'):
                self.reducir(accion)
            elif accion == 'accept':
                print("Análisis completado exitosamente.")
                self.generar_salida()
                return
            else:
                self.manejar_error(estado_actual, token_actual)
                self.generar_salida()
                return

    def obtener_estado_actual(self):
        """Obtiene el estado actual de la pila.

        La pila alterna entre estados (int) y símbolos (Arbol). Este método recorre la pila desde la cima
        hasta encontrar el primer entero, que representa el estado actual.

        Retorna:
            int: El estado actual en la cima de la pila.

        Llamado por:
            analizar()
            reducir()
        """
        contenido_pila = self.pila.mostrar()
        for elemento in reversed(contenido_pila):
            if isinstance(elemento, int):
                return elemento
        raise Exception("No se encontró un estado en la pila.")

    def obtener_accion(self, estado, token):
        """Obtiene la acción desde la tabla LR para un estado y un token dado.

        Busca en la tabla LR la acción que corresponde al estado actual y al token de entrada actual.
        La acción puede ser desplazar , reducir , aceptar o indicar un error.

        Parámetros:
            estado (int): El estado actual en la pila.
            token (str): El token actual en el flujo de entrada.

        Retorna:
            str: La acción correspondiente desde la tabla LR.

        Utiliza:
            self.tabla: La tabla LR cargada previamente.

        Llamado por:
            analizar()
        """
        if token in self.tabla.columns:
            accion = self.tabla.loc[estado, token]
            return str(accion).strip() if pd.notna(accion) else "error"
        else:
            return "error"

    def desplazar(self, accion, token):
        """Realiza una operación de desplazamiento (shift).

        Agrega el token actual y el estado siguiente a la pila, y consume el token del flujo de entrada.

        Parámetros:
            accion (str): La acción obtenida de la tabla LR, por ejemplo, 'd5' para desplazar al estado 5.
            token (str): El token actual que se va a desplazar.

        Llama a:
            self.pila.push()
            self.flujo_entrada.pop()

        Llamado por:
            analizar()
        """
        estado_siguiente = int(accion[1:])
        nodo_token = Arbol(token)
        self.pila.push(nodo_token)
        self.pila.push(estado_siguiente)
        self.flujo_entrada.pop(0)

    def reducir(self, accion):
        """Realiza una operación de reducción (reduce) y construye el árbol de derivación.

        Aplica la regla de reducción indicada por la acción, actualiza la pila y construye los nodos del árbol.

        Parámetros:
            accion (str): La acción obtenida de la tabla LR, por ejemplo, 'r3' para reducir usando la regla 3.

        Llama a:
            obtener_regla()
            self.pila.pop()
            obtener_estado_actual()
            obtener_goto()

        Llamado por:
            analizar()
        """
        numero_regla = int(accion[1:])
        if numero_regla == 0:
            print("Análisis terminado.")
            self.generar_salida()
            exit()
        if numero_regla not in reglas:
            raise KeyError(f"La regla {numero_regla} no está definida en el diccionario de reglas.")

        regla = self.obtener_regla(numero_regla)
        cabecera, cuerpo = regla.split(' ::= ')
        tokens_cuerpo = cuerpo.strip().split()

        nodo_actual = Arbol(cabecera)

        if cuerpo.strip() != '\\e':
            hijos = []
            for _ in range(len(tokens_cuerpo)):
                self.pila.pop()  # Estado
                nodo_hijo = self.pila.pop()  # Símbolo (Arbol)
                hijos.insert(0, nodo_hijo)
            nodo_actual.hijos = hijos

        estado_anterior = self.obtener_estado_actual()
        self.pila.push(nodo_actual)
        estado_siguiente = self.obtener_goto(estado_anterior, cabecera)
        if estado_siguiente == "error":
            self.manejar_error(estado_anterior, cabecera)
            return
        self.pila.push(estado_siguiente)

        if self.arbol is None and cabecera == '<programa>':
            self.arbol = nodo_actual

    def obtener_regla(self, numero_regla):
        """Obtiene una regla de producción por su número.

        Parámetros:
            numero_regla (int): El número de la regla a obtener.

        Retorna:
            str: La regla de producción correspondiente.

        Utiliza:
            reglas: Diccionario global con las reglas de producción.

        Llamado por:
            reducir()
        """
        return reglas[numero_regla]

    def obtener_goto(self, estado, no_terminal):
        """Obtiene el estado GOTO para un no terminal dado desde un estado específico.

        Parámetros:
            estado (int): El estado actual en la pila.
            no_terminal (str): El no terminal para el cual se busca el GOTO.

        Retorna:
            int o str: El estado siguiente si existe, o "error" si no hay transición.

        Utiliza:
            self.tabla: La tabla LR cargada previamente.

        Llamado por:
            reducir()
        """
        simbolo = no_terminal.strip('<>').strip()
        if simbolo in self.tabla.columns:
            goto = self.tabla.loc[estado, simbolo]
            return int(goto) if pd.notna(goto) else "error"
        return "error"

    def manejar_error(self, estado, token):
        """Maneja los errores sintácticos y registra mensajes de error.

        Parámetros:
            estado (int): El estado actual donde ocurrió el error.
            token (str): El token que causó el error.

        Llama a:
            obtener_pila_como_cadena()
            self.salida_proceso.append()

        Llamado por:
            analizar()
            reducir()
        """
        mensaje_error = f"Error: No hay acción para el estado {estado} y el token '{token}'"
        print(mensaje_error)
        pila_str = self.obtener_pila_como_cadena()
        entrada_str = ' '.join(self.flujo_entrada)
        self.salida_proceso.append((pila_str, entrada_str, mensaje_error))
        self.error_ocurrido = True

    def leer_codigo_fuente(self, ruta_archivo):
        """Lee el código fuente desde un archivo y genera la lista de tokens.

        Parámetros:
            ruta_archivo (str): Ruta al archivo que contiene el código fuente.

        Llama a:
            analizador_lexico()

        Llamado por:
            Código principal antes de llamar a analizar()
        """
        with open(ruta_archivo, 'r') as archivo:
            codigo_fuente = archivo.read()
        self.flujo_entrada = self.analizador_lexico(codigo_fuente) + ['$']

    def analizador_lexico(self, codigo_fuente):
        """Analiza el código fuente y genera una lista de tokens.

        Parámetros:
            codigo_fuente (str): El código fuente a analizar.

        Retorna:
            list: Lista de tokens reconocidos en el código fuente.

        Llamado por:
            leer_codigo_fuente()
        """
        patrones = {
            '(': r'\(',
            ')': r'\)',
            '{': r'\{',
            '}': r'\}',
            'tipo': r'\bint\b|\bfloat\b',
            'identificador': r'\b[a-zA-Z_][a-zA-Z0-9_]*\b',
            'entero': r'\b\d+\b',
            'real': r'\b\d+\.\d+\b',
            'cadena': r'\".*?\"',
            'opSuma': r'\+',
            'opMul': r'\*',
            'opRelac': r'<=|>=|<|>',
            'opIgualdad': r'==|!=',
            'opAnd': r'&&',
            'opOr': r'\|\|',
            'opNot': r'!',
            '=': r'=',
            ';': r';',
            ',': r',',
            'if': r'\bif\b',
            'else': r'\belse\b',
            'while': r'\bwhile\b',
            'return': r'\breturn\b',
        }

        tokens = []
        posicion = 0
        longitud_codigo = len(codigo_fuente)

        while posicion < longitud_codigo:
            match = None
            if codigo_fuente[posicion].isspace():
                posicion += 1
                continue

            for token_tipo, patron in patrones.items():
                regex = re.compile(patron)
                match = regex.match(codigo_fuente, posicion)
                if match:
                    tokens.append(token_tipo)
                    posicion = match.end()
                    break

            if not match:
                tokens.append(f"ERROR({codigo_fuente[posicion]})")
                posicion += 1

        return tokens

    def obtener_pila_como_cadena(self):
        """Convierte el contenido de la pila en una cadena para la salida.

        Retorna:
            str: Representación en cadena de los elementos de la pila.

        Utilizado por:
            analizar()
            manejar_error()
            generar_salida()
        """
        elementos_pila = []
        for elemento in self.pila.mostrar():
            if isinstance(elemento, int):
                elementos_pila.append(str(elemento))
            elif isinstance(elemento, Arbol):
                elementos_pila.append(str(elemento.valor))
            else:
                elementos_pila.append(str(elemento))
        return ' '.join(elementos_pila)

    def generar_salida(self):
        """Genera la salida del análisis y el árbol de derivación.

        Crea los archivos 'salida.txt' con los detalles del análisis y 'arbol_derivacion.txt' con el árbol.

        Llama a:
            generar_salida_arbol()

        Llamado por:
            analizar()
            reducir()
            manejar_error()
        """
        with open('salida.txt', 'w') as archivo_salida:
            archivo_salida.write(f"{'Pila'.ljust(100)}{'Entrada'.ljust(40)}{'Salida'}\n")
            for paso in self.salida_proceso:
                pila, entrada, accion = paso
                archivo_salida.write(f"{pila.ljust(100)}{entrada.ljust(40)}{accion}\n")

        if self.arbol:
            with open('arbol_derivacion.txt', 'w') as archivo_arbol:
                archivo_arbol.write(self.generar_salida_arbol(self.arbol))

        print("El análisis ha finalizado. Revisa el archivo 'salida.txt' y 'arbol_derivacion.txt' para ver los detalles.")

    def generar_salida_arbol(self, nodo, nivel=0):
        """Genera una representación del árbol de derivación en formato de texto.

        Parámetros:
            nodo (Arbol): El nodo actual del árbol.
            nivel (int): El nivel de profundidad en el árbol (para indentación).

        Retorna:
            str: Representación en cadena del árbol de derivación.

        Llamado por:
            generar_salida()
            (recursivamente)
        """
        salida = '  ' * nivel + str(nodo.valor) + '\n'
        for hijo in nodo.hijos:
            salida += self.generar_salida_arbol(hijo, nivel + 1)
        return salida

# Definimos las reglas de la gramática
reglas = {
    0: '<Inicial> ::= <programa>',
    1: '<programa> ::= <Definiciones>',
    2: '<Definiciones> ::= \\e',
    3: '<Definiciones> ::= <Definicion> <Definiciones>',
    4: '<Definicion> ::= <DefVar>',
    5: '<Definicion> ::= <DefFunc>',
    6: '<DefVar> ::= tipo identificador <ListaVar> ;',
    7: '<ListaVar> ::= \\e',
    8: '<ListaVar> ::= , identificador <ListaVar>',
    9: '<DefFunc> ::= tipo identificador ( <Parametros> ) <BloqFunc>',
    10: '<Parametros> ::= \\e',
    11: '<Parametros> ::= tipo identificador <ListaParam>',
    12: '<ListaParam> ::= \\e',
    13: '<ListaParam> ::= , tipo identificador <ListaParam>',
    14: '<BloqFunc> ::= { <DefLocales> }',
    15: '<DefLocales> ::= \\e',
    16: '<DefLocales> ::= <DefLocal> <DefLocales>',
    17: '<DefLocal> ::= <DefVar>',
    18: '<DefLocal> ::= <Sentencia>',
    19: '<Sentencias> ::= \\e',
    20: '<Sentencias> ::= <Sentencia> <Sentencias>',
    21: '<Sentencia> ::= identificador = <Expresion> ;',
    22: '<Sentencia> ::= if ( <Expresion> ) <SentenciaBloque> <Otro>',
    23: '<Sentencia> ::= while ( <Expresion> ) <Bloque>',
    24: '<Sentencia> ::= return <ValorRegresa> ;',
    25: '<Sentencia> ::= <LlamadaFunc> ;',
    26: '<Otro> ::= \\e',
    27: '<Otro> ::= else <SentenciaBloque>',
    28: '<Bloque> ::= { <Sentencias> }',
    29: '<ValorRegresa> ::= \\e',
    30: '<ValorRegresa> ::= <Expresion>',
    31: '<Argumentos> ::= \\e',
    32: '<Argumentos> ::= <Expresion> <ListaArgumentos>',
    33: '<ListaArgumentos> ::= \\e',
    34: '<ListaArgumentos> ::= , <Expresion> <ListaArgumentos>',
    35: '<Termino> ::= <LlamadaFunc>',
    36: '<Termino> ::= identificador',
    37: '<Termino> ::= entero',
    38: '<Termino> ::= real',
    39: '<Termino> ::= cadena',
    40: '<LlamadaFunc> ::= identificador ( <Argumentos> )',
    41: '<SentenciaBloque> ::= <Sentencia>',
    42: '<SentenciaBloque> ::= <Bloque>',
    43: '<Expresion> ::= ( <Expresion> )',
    44: '<Expresion> ::= opSuma <Expresion>',
    45: '<Expresion> ::= opNot <Expresion>',
    46: '<Expresion> ::= <Expresion> opMul <Expresion>',
    47: '<Expresion> ::= <Expresion> opSuma <Expresion>',
    48: '<Expresion> ::= <Expresion> opRelac <Expresion>',
    49: '<Expresion> ::= <Expresion> opIgualdad <Expresion>',
    50: '<Expresion> ::= <Expresion> opAnd <Expresion>',
    51: '<Expresion> ::= <Expresion> opOr <Expresion>',
    52: '<Expresion> ::= <Termino>',
}

# Código principal
if __name__ == "__main__":
    # Instanciar el analizador
    analizador = AnalizadorLR('compilador.inf', 'compilador.csv')
    analizador.leer_codigo_fuente('entrada.txt')
    analizador.analizar()
