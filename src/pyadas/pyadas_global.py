import sys
from PySide6.QtWidgets import QApplication
from pyadas.ui.main_window import MainWindow

def pyadasGui():
    """
    Função principal de inicialização da interface gráfica do pyadas.
    Cria a instância do QApplication e exibe a MainWindow.
    """
    # Verifica se já existe uma instância do QApplication (útil se rodar via Jupyter no futuro)
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    
    window = MainWindow()
    window.show()
    
    # Inicia o loop de eventos da interface gráfica
    sys.exit(app.exec())

if __name__ == "__main__":
    # Permite que o arquivo seja testado rodando diretamente pelo terminal
    pyadasGui()