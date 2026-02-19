"""
Assistant View Module
UI for AI consultation interface.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QScrollArea, QFrame, QComboBox, QProgressBar
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QIcon
from pathlib import Path


class AssistantView(QWidget):
    """
    Vue pour la consultation de l'Assistant IA.
    
    Fonctionnalités :
    - UI Premium correspondant au thème générique
    - Interface de chat avec bulles
    - Bannière d'avertissement pour le mode démo
    """
    
    # Signals
    send_requested = Signal(str, str)  # mode, message
    copy_requested = Signal()
    new_conversation_requested = Signal()
    back_requested = Signal()  # Navigate back to search
    
    def __init__(self):
        super().__init__()
        self._setup_ui()
        # No more _apply_styles() - rely on global premium_theme.qss
    
    def _setup_ui(self):
        """Configuration des composants UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(25, 25, 25, 25)
        
        # ============================================
        # HEADER
        # ============================================
        header = QHBoxLayout()
        header.setSpacing(15)
        
        # Back button (Icon style)
        self.back_btn = QPushButton("←")
        self.back_btn.setObjectName("iconButton")
        self.back_btn.setFixedSize(40, 40)
        self.back_btn.setCursor(Qt.PointingHandCursor)
        self.back_btn.setToolTip("Retour")
        self.back_btn.clicked.connect(self.back_requested.emit)
        header.addWidget(self.back_btn)
        
        # Title
        title_layout = QVBoxLayout()
        title_layout.setSpacing(0)
        
        app_title = QLabel('JetSet<span style="color: #ff6b35;">Go</span>')
        app_title.setObjectName("appTitle")
        app_title.setTextFormat(Qt.RichText)
        
        subtitle = QLabel("Assistant Intelligence Artificielle")
        subtitle.setObjectName("subtitle")
        
        title_layout.addWidget(app_title)
        title_layout.addWidget(subtitle)
        header.addLayout(title_layout)
        
        header.addStretch()
        layout.addLayout(header)
        
        # ============================================
        # DEMO BANNER
        # ============================================
        self.demo_banner = self._create_demo_banner()
        layout.addWidget(self.demo_banner)
        
        # ============================================
        # MAIN CONTENT (Glass Panel)
        # ============================================
        main_frame = QFrame()
        main_frame.setObjectName("searchPanel") # Reusing glass panel style
        main_layout = QVBoxLayout(main_frame)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Conversation Area
        self.conversation_scroll = QScrollArea()
        self.conversation_scroll.setWidgetResizable(True)
        self.conversation_scroll.setFrameShape(QFrame.NoFrame)
        self.conversation_scroll.setStyleSheet("background: transparent;")
        
        self.conversation_widget = QWidget()
        self.conversation_widget.setStyleSheet("background: transparent;")
        self.conversation_layout = QVBoxLayout(self.conversation_widget)
        self.conversation_layout.setAlignment(Qt.AlignTop)
        self.conversation_layout.setSpacing(20)
        self.conversation_layout.setContentsMargins(20, 20, 20, 20)
        
        self.conversation_scroll.setWidget(self.conversation_widget)
        main_layout.addWidget(self.conversation_scroll)
        
        layout.addWidget(main_frame, stretch=1)
        
        # ============================================
        # INPUT AREA (Action Panel)
        # ============================================
        input_frame = QFrame()
        input_frame.setObjectName("actionsPanel")
        input_frame.setStyleSheet("""
            QFrame#actionsPanel {
                background: rgba(200, 205, 211, 0.5);
                border-radius: 16px;
                padding: 10px;
            }
        """)
        input_layout = QVBoxLayout(input_frame)
        input_layout.setContentsMargins(15, 15, 15, 15)
        input_layout.setSpacing(10)
        
        # Text Input
        self.message_input = QTextEdit()
        self.message_input.setPlaceholderText("Posez votre question ici...")
        self.message_input.setMinimumHeight(60)
        self.message_input.setMaximumHeight(100)
        self.message_input.setStyleSheet("""
            QTextEdit {
                background: rgba(255, 255, 255, 0.8);
                border: 1px solid rgba(0, 119, 182, 0.3);
                border-radius: 10px;
                padding: 10px;
                font-size: 14px;
                color: #24292f;
            }
            QTextEdit:focus {
                border: 1px solid #0077b6;
                background: #ffffff;
            }
        """)
        self.message_input.textChanged.connect(self._update_char_counter)
        input_layout.addWidget(self.message_input)
        
        # Bottom Bar (Counter + Buttons)
        bottom_bar = QHBoxLayout()
        
        self.char_counter = QLabel("0 / 8000")
        self.char_counter.setStyleSheet("color: #57606a; font-size: 12px;")
        bottom_bar.addWidget(self.char_counter)
        
        bottom_bar.addStretch()
        
        # New Conversation
        self.new_conversation_btn = QPushButton("Nouveau")
        self.new_conversation_btn.setObjectName("secondary")
        self.new_conversation_btn.setCursor(Qt.PointingHandCursor)
        self.new_conversation_btn.clicked.connect(self.new_conversation_requested.emit)
        bottom_bar.addWidget(self.new_conversation_btn)
        
        # Copy
        self.copy_btn = QPushButton("Copier")
        self.copy_btn.setObjectName("secondary")
        self.copy_btn.setCursor(Qt.PointingHandCursor)
        self.copy_btn.setEnabled(False)
        self.copy_btn.clicked.connect(self.copy_requested.emit)
        bottom_bar.addWidget(self.copy_btn)
        
        # Send
        self.send_btn = QPushButton("ENVOYER")
        self.send_btn.setCursor(Qt.PointingHandCursor)
        self.send_btn.clicked.connect(self._on_send_clicked)
        # Apply primary styling explicitly if needed, but theme should handle it
        bottom_bar.addWidget(self.send_btn)
        
        input_layout.addLayout(bottom_bar)
        
        # Progress Bar container (slight overlay or bottom of input)
        self.loading_bar = QProgressBar()
        self.loading_bar.setMaximum(0)
        self.loading_bar.setVisible(False)
        self.loading_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                background: transparent;
                height: 4px;
            }
            QProgressBar::chunk {
                background-color: #0077b6;
                border-radius: 2px;
            }
        """)
        input_layout.addWidget(self.loading_bar)
        
        layout.addWidget(input_frame)
        
        # Status Label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

    def _create_demo_banner(self) -> QFrame:
        """Créer la bannière d'avertissement du mode démo"""
        banner = QFrame()
        banner.setVisible(False)
        banner.setStyleSheet("""
            QFrame {
                background-color: #fff3cd;
                border: 1px solid #ffeeba;
                border-radius: 8px;
                padding: 10px;
                margin-bottom: 10px;
            }
        """)
        
        layout = QHBoxLayout(banner)
        layout.setContentsMargins(10, 5, 10, 5)
        
        icon = QLabel("⚠️")
        layout.addWidget(icon)
        
        text_layout = QVBoxLayout()
        title = QLabel("Mode Démo")
        title.setStyleSheet("font-weight: bold; color: #856404;")
        self.banner_reason_label = QLabel("")
        self.banner_reason_label.setStyleSheet("color: #856404;")
        
        text_layout.addWidget(title)
        text_layout.addWidget(self.banner_reason_label)
        layout.addLayout(text_layout)
        layout.addStretch()
        
        return banner
    
    def _create_message_bubble(self, text: str, is_user: bool, model: str = None) -> QFrame:
        """Crée une bulle de message avec un style premium"""
        bubble = QFrame()
        bubble.setMaximumWidth(700)
        
        if is_user:
            # User Bubble: Brand Blue Gradient
            bubble.setStyleSheet("""
                QFrame {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #0077b6, stop:1 #0096c7);
                    color: white;
                    border-radius: 16px;
                    border-bottom-right-radius: 4px;
                    padding: 15px;
                }
            """)
            bubble.setProperty("alignment", Qt.AlignRight)
        else:
            # AI Bubble: White/Glass
            bubble.setStyleSheet("""
                QFrame {
                    background: rgba(255, 255, 255, 0.9);
                    border: 1px solid rgba(0, 119, 182, 0.2);
                    color: #24292f;
                    border-radius: 16px;
                    border-bottom-left-radius: 4px;
                    padding: 15px;
                }
            """)
            bubble.setProperty("alignment", Qt.AlignLeft)
        
        bubble_layout = QVBoxLayout(bubble)
        
        # Message text
        message_label = QLabel(text)
        message_label.setWordWrap(True)
        message_label.setFont(QFont("Segoe UI", 11))
        message_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        if is_user:
            message_label.setStyleSheet("background: transparent; color: white;")
        else:
            message_label.setStyleSheet("background: transparent; color: #24292f;")
            
        bubble_layout.addWidget(message_label)
        
        # Model info
        if not is_user and model:
            model_info = QLabel(f"✨ {model}")
            model_info.setStyleSheet("background: transparent; color: #0077b6; font-size: 10px; font-weight: 600; margin-top: 5px;")
            model_info.setAlignment(Qt.AlignRight)
            bubble_layout.addWidget(model_info)
            
        # Wrapper
        wrapper = QWidget()
        wrapper_layout = QHBoxLayout(wrapper)
        wrapper_layout.setContentsMargins(0, 0, 0, 0)
        
        if is_user:
            wrapper_layout.addStretch()
            wrapper_layout.addWidget(bubble)
        else:
            wrapper_layout.addWidget(bubble)
            wrapper_layout.addStretch()
            
        return wrapper

    # ============================================
    # KEEP EXISTING LOGIC (Unchanged)
    # ============================================
    
    def _update_char_counter(self):
        char_count = len(self.message_input.toPlainText())
        self.char_counter.setText(f"{char_count} / 8000")
        if char_count > 8000:
            self.char_counter.setStyleSheet("color: #dc3545; font-weight: bold;")
            self.send_btn.setEnabled(False)
        else:
            self.char_counter.setStyleSheet("color: #57606a;")
            self.send_btn.setEnabled(not self.loading_bar.isVisible())

    def _on_send_clicked(self):
        message = self.message_input.toPlainText().strip()
        if not message:
            self.show_error("Veuillez entrer un message")
            return
        self.send_requested.emit("free", message)

    def add_user_message(self, message: str):
        bubble = self._create_message_bubble(message, is_user=True)
        self.conversation_layout.addWidget(bubble)
        self._scroll_to_bottom()

    def add_ai_message(self, message: str, model: str = "unknown"):
        bubble = self._create_message_bubble(message, is_user=False, model=model)
        self.conversation_layout.addWidget(bubble)
        self._scroll_to_bottom()
        self.copy_btn.setEnabled(True)

    def _scroll_to_bottom(self):
        scrollbar = self.conversation_scroll.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def show_demo_banner(self, reason: str = ""):
        self.demo_banner.setVisible(True)
        reason_map = {
            "ollama_unreachable": "Ollama n'est pas accessible.",
            "ollama_unavailable": "Ollama n'est pas installé.",
            "unexpected_error": "Erreur de connexion."
        }
        self.banner_reason_label.setText(reason_map.get(reason, reason))

    def hide_demo_banner(self):
        self.demo_banner.setVisible(False)

    def set_loading(self, loading: bool):
        self.loading_bar.setVisible(loading)
        self.send_btn.setEnabled(not loading)
        self.message_input.setEnabled(not loading)

    def show_error(self, error: str):
        self.status_label.setText(f"❌ {error}")
        self.status_label.setStyleSheet("color: #dc3545; font-weight: bold;")
        # Also re-enable input if error occurred
        self.set_loading(False)

    def show_success(self, message: str):
        self.status_label.setText(f"✅ {message}")
        self.status_label.setStyleSheet("color: #28a745; font-weight: bold;")

    def clear_status(self):
        self.status_label.setText("")

    def clear_conversation(self):
        while self.conversation_layout.count():
            item = self.conversation_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.copy_btn.setEnabled(False)
        self.message_input.clear()
        self.hide_demo_banner()
