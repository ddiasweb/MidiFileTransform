from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QLineEdit,
    QVBoxLayout, QHBoxLayout, QFileDialog, QMessageBox, QComboBox,
    QCheckBox, QGridLayout, QGroupBox, QFormLayout, QSlider
)
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QCloseEvent
from mido import MidiFile, MidiTrack, open_output
import mido.backends.rtmidi
import sys
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import time
import threading

GM_INSTRUMENTS = [
    # Piano
    "Piano de Concerto", "Piano Brilhante", "Piano Elétrico", "Piano Honky-Tonk",
    "Piano Rhodes", "Piano com Chorus", "Cravo", "Clavinet",

    # Percussão Cromática
    "Celesta", "Glockenspiel", "Caixa de Música", "Vibrafone",
    "Marimba", "Xilofone", "Sinos Tubulares", "Dulcimer",

    # Órgãos
    "Órgão Hammond", "Órgão Percussivo", "Órgão Rock", "Órgão de Igreja",
    "Órgão de Palhetas", "Acordeão", "Harmônica", "Acordeão Tango",

    # Guitarras
    "Violão de Nylon", "Violão de Aço", "Guitarra Jazz Elétrica", "Guitarra Limpa Elétrica",
    "Guitarra Mutada Elétrica", "Guitarra Overdrive", "Guitarra com Distorção", "Harmônicos de Guitarra",

    # Baixos
    "Baixo Acústico", "Baixo Elétrico com Dedos", "Baixo Elétrico com Palheta", "Baixo Fretless",
    "Baixo Slap 1", "Baixo Slap 2", "Baixo Sintetizado 1", "Baixo Sintetizado 2",

    # Cordas
    "Violino", "Viola", "Violoncelo", "Contrabaixo",
    "Cordas com Tremolo", "Cordas Pizzicato", "Harpa Orquestral", "Tímpano",

    # Conjuntos
    "Ensemble de Cordas 1", "Ensemble de Cordas 2", "Cordas Sintetizadas 1", "Cordas Sintetizadas 2",
    "Coro Aahs", "Vozes Oohs", "Voz Sintetizada", "Orquestra Hit",

    # Metais
    "Trompete", "Trombone", "Tuba", "Trompete com Surdina",
    "Trompa", "Seção de Metais", "Metais Sintetizados 1", "Metais Sintetizados 2",

    # Palhetas
    "Sax Soprano", "Sax Alto", "Sax Tenor", "Sax Barítono",
    "Oboé", "Corne Inglês", "Fagote", "Clarinete",

    # Sopros
    "Píccolo", "Flauta", "Flauta Doce", "Flauta Pan",
    "Garrafa Soprada", "Shakuhachi", "Assobio", "Ocarina",

    # Leads Sintetizados
    "Lead Quadrado", "Lead Dente de Serra", "Lead Calliope", "Lead Chiff",
    "Lead Charang", "Lead Voz", "Lead Quintas", "Lead Baixo + Lead",

    # Pads Sintetizados
    "Pad New Age", "Pad Quente", "Pad Polissintético", "Pad Coral",
    "Pad Arco", "Pad Metálico", "Pad Halo", "Pad Sweep",

    # Efeitos Sintetizados
    "Efeito Chuva", "Efeito Trilha Sonora", "Efeito Cristal", "Efeito Atmosfera",
    "Efeito Brilho", "Efeito Goblins", "Efeito Ecos", "Efeito Sci-Fi",

    # Étnicos
    "Sitar", "Banjo", "Shamisen", "Koto",
    "Kalimba", "Gaita de Foles", "Rabeca", "Shanai",

    # Percussivos
    "Sino Tinkle", "Agogô", "Steel Drums", "Bloco de Madeira",
    "Tambor Taiko", "Tom Melódico", "Bateria Sintetizada", "Címbalo Reverso",

    # Efeitos Sonoros
    "Ruído de Traste de Guitarra", "Ruído de Respiração", "Som de Praia", "Canto de Pássaro",
    "Toque de Telefone", "Helicóptero", "Aplausos", "Tiro"
]

foregound_colors = [
    '#00FF00',  # lime
    '#00FFFF',  # cyan
    '#FF00FF',  # magenta
    '#FFA500',  # orange
    '#800080',  # purple
    '#FF69B4',  # pink
    '#FF0000',  # red
    '#1E90FF',  # blue
    '#00FA9A',  # medium spring green
    '#8B4513',  # saddle brown
    '#A9A9A9',  # dark gray
    '#008080',  # teal
    '#000080',  # navy
    '#808000',  # olive
    '#B22222',  # firebrick
    '#7CFC00'   # lawn green
]

background_colors = [
    '#003300',  # dark green
    '#003333',  # dark cyan
    '#330033',  # dark magenta
    '#331A00',  # dark orange
    '#1A001A',  # dark purple
    '#331A1A',  # dark pink
    '#330000',  # dark red
    '#001A33',  # dark blue
    '#00331A',  # dark medium spring green
    '#331900',  # dark saddle brown
    '#1A1A1A',  # very dark gray
    '#003333',  # dark teal
    '#000033',  # dark navy
    '#333300',  # dark olive
    '#331919',  # dark firebrick
    '#193300'   # dark lawn green
]

class MidiFileTransform(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Midi File Transform 🎼")
        self.setGeometry(100, 100, 500, 400)
        self.setMinimumSize(800, 600)

        self.midi_path = ""
        self.mid = ""
        self.programs = {}
        self.channel_notes = {}
        self.channel_times = {}

        self.canais_visiveis = []
        self.repro_timer = QTimer()
        self._stop_flag = False
        self.thread = None
        self.output = open_output()

        self._setup_widgets()
        self._setup_layouts()

    def closeEvent(self, event: QCloseEvent):
        self.stop()
        event.accept()

    def _setup_widgets(self):
        # Botões principais
        self.botao_play = QPushButton("▶️ Play")
        self.botao_play.setEnabled(False)
        self.botao_play.clicked.connect(self.play)
        self.botao_stop = QPushButton("⏹️ Stop")
        self.botao_stop.setEnabled(False)
        self.botao_stop.clicked.connect(self.stop)
        self.select_button = QPushButton("Selecionar Arquivo MIDI")
        self.select_button.clicked.connect(self.selecionar_arquivo)
        self.duracao_label = QLabel("Duração:")
        self.canvas = FigureCanvas(Figure(figsize=(5, 3)))
        self.canvas.figure.set_facecolor(background_colors[10])
        self.canal_origem = QComboBox()
        self.canal_destino = QComboBox()
        self.volume_input = QSlider()
        self.volume_input.setValue(100)
        self.volume_input.setRange(0, 100)
        self.volume_input.actionTriggered.connect(lambda: self.volume_input_label.setText(str(self.volume_input.value()) + "%"))
        self.volume_input_label = QLabel()
        self.volume_input_label.setText("100%")
        self.move_button = QPushButton("Mover Canal")
        self.move_button.clicked.connect(self.executar_move)
        self.volume_button = QPushButton("Alterar Volume")
        self.volume_button.clicked.connect(self.executar_volume)
        self.canal_group = QGroupBox("🎚 Canais")
        self.channels_checkboxes_grid = QGridLayout()
        self.canal_group.setLayout(self.channels_checkboxes_grid)
        self.canal_checkboxes = []

    def _setup_layouts(self):
        main_layout = QHBoxLayout()
        sidebar_layout = QVBoxLayout()
        content_layout = QVBoxLayout()

        # Barra lateral
        sidebar_layout.addWidget(self._create_file_group())
        sidebar_layout.addWidget(self.canal_group)
        main_layout.addLayout(sidebar_layout)

        # Conteúdo principal
        content_layout.addWidget(self._create_player_group())
        content_layout.addWidget(self._create_grafico_group())
        content_layout.addLayout(self._create_canal_volume_layout())
        main_layout.addLayout(content_layout)

        self.setLayout(main_layout)

    def _create_file_group(self):
        file_group = QGroupBox("🎵 Arquivo")
        file_layout = QVBoxLayout()
        file_layout.addWidget(self.select_button)
        file_layout.addWidget(self.duracao_label)
        file_group.setLayout(file_layout)
        return file_group

    def _create_player_group(self):
        player_group = QGroupBox("⏯ Controle")
        player_layout = QHBoxLayout()
        player_layout.addWidget(self.botao_play)
        player_layout.addWidget(self.botao_stop)
        player_group.setLayout(player_layout)
        return player_group

    def _create_grafico_group(self):
        grafico_group = QGroupBox("📈 Visualização")
        grafico_layout = QVBoxLayout()
        grafico_layout.addWidget(self.canvas)
        grafico_group.setLayout(grafico_layout)
        return grafico_group

    def _create_canal_volume_layout(self):
        canal_volume_layout = QHBoxLayout()
        # Canal origem/destino
        canal_transform_group = QGroupBox("🔁 Canal")
        canal_transform_layout = QFormLayout()
        canal_transform_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        canal_transform_layout.addRow("Origem:", self.canal_origem)
        canal_transform_layout.addRow("Destino:", self.canal_destino)
        canal_transform_layout.addRow(self.move_button)
        canal_transform_group.setLayout(canal_transform_layout)
        canal_volume_layout.addWidget(canal_transform_group)
        # Volume
        volume_group = QGroupBox("🔊 Volume")
        volume_layout = QHBoxLayout()
        volume_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        volume_layout.addWidget(self.volume_input)
        volume_layout.addWidget(self.volume_input_label)
        volume_layout.addWidget(self.volume_button)
        volume_group.setLayout(volume_layout)
        canal_volume_layout.addWidget(volume_group)
        return canal_volume_layout

    def selecionar_arquivo(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Selecione um arquivo MIDI", "", "MIDI Files (*.mid)")
        if file_name:
            self.midi_path = file_name
            self.update_midi()

    def atualizar_playhead(self):
        tempo_atual = time.time() - self.tempo_inicio
        self.playhead.set_xdata([tempo_atual])
        self.canvas.draw()

    def play(self):
        self.botao_play.setEnabled(False)
        self.botao_stop.setEnabled(True)
        if self.thread and self.thread.is_alive():
            return
        self._stop_flag = False
        self.thread = threading.Thread(target=self._play_loop)
        self.thread.start()
        self.repro_timer.timeout.connect(self.atualizar_playhead)
        self.tempo_inicio = time.time()
        self.repro_timer.start(50)

    def stop(self):
        self.botao_play.setEnabled(True)
        self.botao_stop.setEnabled(False)
        self._stop_flag = True
        if self.thread:
            self.thread.join()
        self.repro_timer.stop()

    def _play_loop(self):
        for msg in self.mid.play():
            if 'channel' in msg.dict() and msg.channel in self.canais_visiveis:
                if self._stop_flag:
                    self.output.reset()
                    break
                if not msg.is_meta:
                    self.output.send(msg)

    def update_midi(self):
        
        self.stop()
        self.mid = MidiFile(self.midi_path)

        self.channel_notes = {i: [] for i in range(16)}
        self.channel_times = {i: [] for i in range(16)}
        self.programs = {}

        time_acc = 0
        for msg in self.mid:
            time_acc += msg.time
            if msg.type == "note_on":
                canal = msg.channel
                self.channel_notes[canal].append(msg.note)
                self.channel_times[canal].append(time_acc)
            if msg.type == "program_change":
                self.programs[msg.channel] = msg.program

        self.clearLayout(self.channels_checkboxes_grid)
        self.canal_checkboxes.clear()

        for i in range(16):
            program = self.programs.get(i, 0)
            program_name = GM_INSTRUMENTS[program] if program < len(GM_INSTRUMENTS) else f"Instrumento {program}"

            check = QCheckBox(f"Canal {i} – {program_name}")
            self.canal_checkboxes.append(check)

            if i in self.programs:
                check.stateChanged.connect(self.update_visible_channels)

                cor_label = QLabel()
                cor_label.setFixedSize(12, 12)
                cor_label.setStyleSheet(f"""
                    background-color: {foregound_colors[i]};
                    border-radius: 6px;
                    border: 1px solid {background_colors[i]};
                """)
                cor_label.setContentsMargins(0, 0, 0, 0)

                linha_layout = QHBoxLayout()
                linha_layout.addWidget(check)
                linha_layout.addWidget(cor_label)
                linha_layout.addStretch()
                linha_layout.setSpacing(4)
                linha_layout.setContentsMargins(0, 0, 0, 0)

                linha_widget = QWidget()
                linha_widget.setLayout(linha_layout)
                linha_widget.setContentsMargins(0, 0, 0, 0)

                self.channels_checkboxes_grid.addWidget(linha_widget)


        segundos = self.mid.length
        minutos = int(segundos) // 60
        segundos = int(segundos) % 60
        self.duracao_label.setText(f"Duração: {minutos} min {segundos} s")

        self.botao_play.setEnabled(True)
        self.canais_visiveis.clear()
        self.atualizar_interface()

    def update_visible_channels(self):
        self.canais_visiveis = [i for i, check in enumerate(self.canal_checkboxes) if check.isChecked()]
        self.atualizar_interface()

    def clearLayout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    self.clearLayout(item.layout())

    def atualizar_interface(self):

        self.canal_origem.clear()
        self.canal_destino.clear()

        # Limpa e configura o gráfico
        self.canvas.figure.clear()
        ax = self.canvas.figure.add_subplot()

        # 🎨 Estilo HUD
        self.canvas.figure.set_facecolor(background_colors[10])
        ax.set_facecolor(background_colors[10])

        # Remove eixos e ticks
        ax.yaxis.set_visible(False)
        ax.xaxis.set_visible(False)
        ax.set_xticks([])
        ax.set_yticks([])

        # Remove padding
        self.canvas.figure.subplots_adjust(left=0, right=1, top=1, bottom=0)
        ax.margins(x=0, y=0)

        # Linha de reprodução estilo laser
        self.playhead = ax.axvline(x=0, color='cyan', linestyle='--', linewidth=1.5)

        # Plotagem com estilo neon
        for canal in range(16):
            prog = self.programs.get(canal, 0)
            nome = GM_INSTRUMENTS[prog] if prog < len(GM_INSTRUMENTS) else f"Instrumento {prog}"

            if canal in self.canais_visiveis:
                self.canal_origem.addItem(f"Canal {canal} → {nome}", canal)
                ax.scatter(
                    self.channel_times[canal],
                    self.channel_notes[canal],
                    s=8,
                    label=f"{nome}",
                    color=foregound_colors[canal]
                )
            else:
                self.canal_destino.addItem(f"Canal {canal}", canal)

        # Atualiza o canvas
        self.canvas.draw()        


    def executar_move(self):
        try:
            canal_origem = int(self.canal_origem.currentData())
            canal_destino = int(self.canal_destino.currentData())
            nova_mid = MidiFile(ticks_per_beat=self.mid.ticks_per_beat)
            for track in self.mid.tracks:
                nova_track = MidiTrack()
                nova_mid.tracks.append(nova_track)
                for msg in track:
                    if hasattr(msg, 'channel') and msg.channel == canal_origem:
                        msg = msg.copy(channel=canal_destino, time=msg.time)
                    else:
                        msg = msg.copy(time=msg.time)
                    nova_track.append(msg)
            nova_mid.save(self.midi_path)
            QMessageBox.information(self, "Sucesso", "Canal movido e arquivo salvo.")
            self.update_midi()
        except Exception as e:
            QMessageBox.critical(self, "Erro", str(e))

    def executar_volume(self):
        try:
            volume_fator = float(self.volume_input.value()) / 100.0
            nova_mid = MidiFile(ticks_per_beat=self.mid.ticks_per_beat)
            for track in self.mid.tracks:
                nova_track = MidiTrack()
                nova_mid.tracks.append(nova_track)
                for msg in track:
                    if msg.type == "note_on":
                        vel = max(1, min(127, int(msg.velocity * volume_fator)))
                        msg = msg.copy(velocity=vel, time=msg.time)
                    elif msg.type == "control_change" and msg.control == 7:
                        val = max(1, min(127, int(msg.value * volume_fator)))
                        msg = msg.copy(value=val, time=msg.time)
                    else:
                        msg = msg.copy(time=msg.time)
                    nova_track.append(msg)
            nova_mid.save(self.midi_path)
            QMessageBox.information(self, "Sucesso", "Volume alterado e arquivo salvo.")
            self.update_midi()
        except Exception as e:
            QMessageBox.critical(self, "Erro", str(e)

)

def run():
    app = QApplication(sys.argv)
    window = MidiFileTransform()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    run()