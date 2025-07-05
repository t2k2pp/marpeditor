
import customtkinter as ctk
from src.controllers.app_controller import AppController
from src.views.main_app_view import MainAppView

if __name__ == "__main__":
    app_controller = AppController()
    app_view = MainAppView(app_controller)
    app_view.mainloop()
