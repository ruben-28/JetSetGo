"""
Assistant View Module
UI for AI consultation interface.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QScrollArea, QFrame, QComboBox, QProgressBar
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont


class AssistantView(QWidget):
    """
    View for AI Assistant consultation.
    
    Features:
    - Mode selector (compare, budget, policy, free)
    - Chat interface with bubbles
    - Demo mode warning banner
    - Copy response button
    - New conversation button
    """
    
    # Signals
    send_requested = Signal(str, str)  # mode, message
    copy_requested = Signal()
    new_conversation_requested = Signal()
    back_requested = Signal()  # Navigate back to search
    
    def __init__(self):
        super().__init__()
        self._setup_ui()
        self._apply_styles()
    
    def _setup_ui(self):
        """Setup UI components"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Header with back button
        header_layout = QHBoxLayout()
        
        # Back button
        self.back_btn = QPushButton("← Retour")
        self.back_btn.setObjectName("secondary")
        self.back_btn.setMinimumHeight(40)
        self.back_btn.setMaximumWidth(120)
        self.back_btn.clicked.connect(self.back_requested.emit)
        header_layout.addWidget(self.back_btn)
        
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Header
        header_label = QLabel("Assistant IA JetSetGo")
        header_label.setObjectName("header")
        header_label.setFont(QFont("Segoe UI", 24, QFont.Bold))
        layout.addWidget(header_label)
        
        # Demo banner (hidden by default)
        self.demo_banner = self._create_demo_banner()
        layout.addWidget(self.demo_banner)
        
        # Mode selector
        mode_layout = QHBoxLayout()
        mode_label = QLabel("Mode:")
        mode_label.setFont(QFont("Segoe UI", 11))
        self.mode_selector = QComboBox()
        self.mode_selector.addItems([
            "Comparer des offres",
            "Conseil budget",
            "Expliquer politique",
            "Question libre"
        ])
        self.mode_selector.setMinimumWidth(250)
        mode_layout.addWidget(mode_label)
        mode_layout.addWidget(self.mode_selector)
        mode_layout.addStretch()
        layout.addLayout(mode_layout)
        
        # Conversation area
        self.conversation_scroll = QScrollArea()
        self.conversation_scroll.setWidgetResizable(True)
        self.conversation_scroll.setMinimumHeight(350)
        self.conversation_widget = QWidget()
        self.conversation_layout = QVBoxLayout(self.conversation_widget)
        self.conversation_layout.setAlignment(Qt.AlignTop)
        self.conversation_layout.setSpacing(15)
        self.conversation_scroll.setWidget(self.conversation_widget)
        layout.addWidget(self.conversation_scroll)
        
        # Input area
        input_layout = QVBoxLayout()
        input_label = QLabel("Votre message:")
        input_label.setFont(QFont("Segoe UI", 10))
        self.message_input = QTextEdit()
        self.message_input.setPlaceholderText(
            "Posez votre question ici (max 8000 caractères)..."
        )
        self.message_input.setMinimumHeight(100)
        self.message_input.setMaximumHeight(150)
        self.char_counter = QLabel("0 / 8000")
        self.char_counter.setFont(QFont("Segoe UI", 9))
        self.message_input.textChanged.connect(self._update_char_counter)
        
        input_layout.addWidget(input_label)
        input_layout.addWidget(self.message_input)
        input_layout.addWidget(self.char_counter, alignment=Qt.AlignRight)
        layout.addLayout(input_layout)
        
        # Loading indicator
        self.loading_bar = QProgressBar()
        self.loading_bar.setMaximum(0)  # Indeterminate
        self.loading_bar.setVisible(False)
        layout.addWidget(self.loading_bar)
        
        # Action buttons
        buttons_layout = QHBoxLayout()
        
        self.send_btn = QPushButton("Envoyer")
        self.send_btn.setMinimumHeight(45)
        self.send_btn.setObjectName("primary")
        self.send_btn.clicked.connect(self._on_send_clicked)
        
        self.copy_btn = QPushButton("Copier réponse")
        self.copy_btn.setMinimumHeight(45)
        self.copy_btn.setEnabled(False)
        self.copy_btn.clicked.connect(self.copy_requested.emit)
        
        self.new_conversation_btn = QPushButton("Nouvelle conversation")
        self.new_conversation_btn.setMinimumHeight(45)
        self.new_conversation_btn.clicked.connect(self.new_conversation_requested.emit)
        
        buttons_layout.addWidget(self.send_btn, 2)
        buttons_layout.addWidget(self.copy_btn, 1)
        buttons_layout.addWidget(self.new_conversation_btn, 1)
        layout.addLayout(buttons_layout)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setFont(QFont("Segoe UI", 9))
        self.status_label.setStyleSheet("color: #666;")
        layout.addWidget(self.status_label)
    
    def _create_demo_banner(self) -> QFrame:
        """Create demo mode warning banner"""
        banner = QFrame()
        banner.setVisible(False)
        banner.setStyleSheet("""
            QFrame {
                background-color: #fff3cd;
                border: 2px solid #ffc107;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        
        banner_layout = QVBoxLayout(banner)
        banner_label = QLabel("Mode Démo - Ollama indisponible")
        banner_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        banner_label.setStyleSheet("color: #856404;")
        
        self.banner_reason_label = QLabel("")
        self.banner_reason_label.setStyleSheet("color: #856404;")
        self.banner_reason_label.setWordWrap(True)
        
        banner_layout.addWidget(banner_label)
        banner_layout.addWidget(self.banner_reason_label)
        
        return banner
    
    def _update_char_counter(self):
        """Update character counter"""
        char_count = len(self.message_input.toPlainText())
        self.char_counter.setText(f"{char_count} / 8000")
        
        # Disable send button if over limit
        if char_count > 8000:
            self.char_counter.setStyleSheet("color: #dc3545; font-weight: bold;")
            self.send_btn.setEnabled(False)
        else:
            self.char_counter.setStyleSheet("")
            self.send_btn.setEnabled(not self.loading_bar.isVisible())
    
    def _on_send_clicked(self):
        """Handle send button click"""
        message = self.message_input.toPlainText().strip()
        if not message:
            self.show_error("Veuillez entrer un message")
            return
        
        mode_map = {
            "Comparer des offres": "compare",
            "Conseil budget": "budget",
            "Expliquer politique": "policy",
            "Question libre": "free"
        }
        mode = mode_map[self.mode_selector.currentText()]
        
        self.send_requested.emit(mode, message)
    
    def add_user_message(self, message: str):
        """Add user message to conversation"""
        bubble = self._create_message_bubble(message, is_user=True)
        self.conversation_layout.addWidget(bubble)
        self._scroll_to_bottom()
    
    def add_ai_message(self, message: str, model: str = "unknown"):
        """Add AI message to conversation"""
        bubble = self._create_message_bubble(message, is_user=False, model=model)
        self.conversation_layout.addWidget(bubble)
        self._scroll_to_bottom()
        self.copy_btn.setEnabled(True)
    
    def _create_message_bubble(self, text: str, is_user: bool, model: str = None) -> QFrame:
        """Create a message bubble"""
        bubble = QFrame()
        bubble.setMaximumWidth(600)
        
        if is_user:
            bubble.setStyleSheet("""
                QFrame {
                    background-color: #007bff;
                    color: white;
                    border-radius: 15px;
                    padding: 15px;
                }
            """)
            bubble.setProperty("alignment", Qt.AlignRight)
        else:
            bubble.setStyleSheet("""
                QFrame {
                    background-color: #f1f3f5;
                    color: #212529;
                    border-radius: 15px;
                    padding: 15px;
                }
            """)
            bubble.setProperty("alignment", Qt.AlignLeft)
        
        bubble_layout = QVBoxLayout(bubble)
        bubble_layout.setSpacing(8)
        
        # Message text
        message_label = QLabel(text)
        message_label.setWordWrap(True)
        message_label.setFont(QFont("Segoe UI", 10))
        if is_user:
            message_label.setStyleSheet("color: white;")
        bubble_layout.addWidget(message_label)
        
        # Model info for AI messages
        if not is_user and model:
            model_label = QLabel(f"Modèle: {model}")
            model_label.setFont(QFont("Segoe UI", 8))
            model_label.setStyleSheet("color: #6c757d; font-style: italic;")
            bubble_layout.addWidget(model_label)
        
        # Wrapper for alignment
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
    
    def _scroll_to_bottom(self):
        """Scroll conversation to bottom"""
        scrollbar = self.conversation_scroll.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def show_demo_banner(self, reason: str = ""):
        """Show demo mode banner"""
        self.demo_banner.setVisible(True)
        
        reason_map = {
            "ollama_unreachable": "Ollama n'est pas accessible. Démarrez-le avec: ollama serve",
            "ollama_unavailable": "Ollama n'est pas installé ou configuré",
            "unexpected_error": "Erreur inattendue lors de la connexion à Ollama"
        }
        
        reason_text = reason_map.get(reason, "Le service LLM n'est pas disponible")
        self.banner_reason_label.setText(reason_text)
    
    def hide_demo_banner(self):
        """Hide demo mode banner"""
        self.demo_banner.setVisible(False)
    
    def set_loading(self, loading: bool):
        """Set loading state"""
        self.loading_bar.setVisible(loading)
        self.send_btn.setEnabled(not loading)
        self.message_input.setEnabled(not loading)
        self.mode_selector.setEnabled(not loading)
    
    def show_error(self, error: str):
        """Show error message"""
        self.status_label.setText(f"❌ {error}")
        self.status_label.setStyleSheet("color: #dc3545; font-weight: bold;")
    
    def show_success(self, message: str):
        """Show success message"""
        self.status_label.setText(f"✅ {message}")
        self.status_label.setStyleSheet("color: #28a745;")
    
    def clear_status(self):
        """Clear status message"""
        self.status_label.setText("")
    
    def clear_conversation(self):
        """Clear all messages"""
        while self.conversation_layout.count():
            item = self.conversation_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.copy_btn.setEnabled(False)
        self.message_input.clear()
        self.hide_demo_banner()
    
    def get_message(self) -> str:
        """Get current message text"""
        return self.message_input.toPlainText().strip()
    
    def set_mode(self, index: int):
        """Set consultation mode by index"""
        self.mode_selector.setCurrentIndex(index)
    
    def set_message(self, text: str):
        """Set message input text"""
        self.message_input.setPlainText(text)
    
    def _apply_styles(self):
        """Apply custom styles"""
        self.setStyleSheet("""
            QWidget {
                background-color: #1a1d29;
                color: #e8eaed;
            }
            #header {
                color: #4dabf7;
                padding: 10px;
            }
            QComboBox {
                background-color: #2d3142;
                color: #e8eaed;
                border: 2px solid #4dabf7;
                border-radius: 8px;
                padding: 8px;
                font-size: 11pt;
            }
            QTextEdit {
                background-color: #2d3142;
                color: #e8eaed;
                border: 2px solid #4dabf7;
                border-radius: 8px;
                padding: 10px;
                font-size: 10pt;
            }
            QPushButton {
                background-color: #4dabf7;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 11pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #339af0;
            }
            QPushButton:pressed {
                background-color: #1c7ed6;
            }
            QPushButton:disabled {
                background-color: #495057;
                color: #adb5bd;
            }
            QPushButton#primary {
                background-color: #51cf66;
            }
            QPushButton#primary:hover {
                background-color: #40c057;
            }
            QPushButton#secondary {
                background-color: #495057;
            }
            QPushButton#secondary:hover {
                background-color: #6c757d;
            }
            QScrollArea {
                background-color: #2d3142;
                border: 2px solid #4dabf7;
                border-radius: 8px;
            }
            QProgressBar {
                background-color: #2d3142;
                border: 2px solid #4dabf7;
                border-radius: 4px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4dabf7;
            }
        """)
