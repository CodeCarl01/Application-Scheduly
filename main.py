import flet as ft
import datetime
import threading
import time as tm
import os
import json
import locale

# Définir la locale en français pour afficher les mois en français
locale.setlocale(locale.LC_TIME, 'fr_FR')
from datetime import datetime,time , timedelta, date
from dataclasses import dataclass
from typing import Optional, Dict, List



@dataclass
class TimeSlot:
    start_time: time
    end_time: time
    course: str
    is_temporary: bool = False


class ScheduleManager:
    def __init__(self):
        self.schedule: Dict[str, List[TimeSlot]] = {
            "LUNDI": [], "MARDI": [], "MERCREDI": [], "JEUDI": [],
            "VENDREDI": [], "SAMEDI": [], "DIMANCHE": []
        }
        # Définir les heures de début et de fin de la journée
        self.day_start = time(6, 0)  # 6h00
        self.day_end = time(0, 0)  # 24h00 (minuit)
        self.time_slots = self._generate_time_slots()
        self.load_schedule()
        self.remove_past_temporary_events()

    def _generate_time_slots(self) -> List[str]:
        """Génère une liste de créneaux horaires standards sous la forme '6h-7h'."""
        slots = []
        current = datetime.combine(date.today(), self.day_start)
        end = datetime.combine(date.today() + timedelta(days=1), self.day_end)

        while current < end:
            next_hour = current + timedelta(hours=1)
            slots.append(f"{current.strftime('%Hh')}-{next_hour.strftime('%Hh')}")
            current = next_hour
        return slots

    def add_time_slot(self, day: str, start_time: time, end_time: time,
                      course: str, is_temporary: bool = False) -> bool:
        """Ajoute un créneau horaire dans l'emploi du temps."""
        if day not in self.schedule:
            return False

        # Ajuster end_time si nécessaire pour gérer minuit
        if end_time == time(0, 0):
            end_time = time(23, 59)

        # Vérifier que les heures sont dans la plage valide
        if (start_time < self.day_start or start_time >= end_time):
            return False

        new_slot = TimeSlot(start_time, end_time, course, is_temporary)

        # Vérifie les conflits
        for slot in self.schedule[day]:
            if (start_time < slot.end_time and end_time > slot.start_time):
                return False

        self.schedule[day].append(new_slot)
        self.schedule[day].sort(key=lambda x: x.start_time)
        self.save_schedule()
        return True

    def remove_time_slot(self, day: str, start_time: time) -> bool:
        """Supprime un créneau horaire basé sur son heure de début."""
        if day not in self.schedule:
            return False

        original_length = len(self.schedule[day])
        self.schedule[day] = [slot for slot in self.schedule[day]
                              if slot.start_time != start_time]

        if len(self.schedule[day]) != original_length:
            self.save_schedule()
            return True
        return False

    def save_schedule(self):
        """Sauvegarde l'emploi du temps dans un fichier JSON."""
        schedule_dict = {}
        for day, slots in self.schedule.items():
            schedule_dict[day] = [
                {
                    "start_time": slot.start_time.strftime("%H:%M"),
                    "end_time": slot.end_time.strftime("%H:%M"),
                    "course": slot.course,
                    "is_temporary": slot.is_temporary
                } for slot in slots
            ]
        with open("schedule.json", "w", encoding='utf-8') as f:
            json.dump(schedule_dict, f, ensure_ascii=False, indent=2)

    def load_schedule(self):
        """Charge l'emploi du temps depuis le fichier JSON."""
        try:
            with open("schedule.json", "r", encoding='utf-8') as f:
                schedule_dict = json.load(f)
                for day, slots in schedule_dict.items():
                    self.schedule[day] = [
                        TimeSlot(
                            datetime.strptime(slot["start_time"], "%H:%M").time(),
                            datetime.strptime(slot["end_time"], "%H:%M").time(),
                            slot["course"],
                            slot["is_temporary"]
                        ) for slot in slots
                    ]
        except FileNotFoundError:
            pass

    def remove_past_temporary_events(self):
        """Supprime les événements temporaires passés."""
        current_datetime = datetime.now()
        for day in self.schedule.keys():
            self.schedule[day] = [
                slot for slot in self.schedule[day]
                if not (slot.is_temporary and
                        datetime.combine(date.today(), slot.end_time) < current_datetime)
            ]
        self.save_schedule()




# Fonction principale de l'application
def main(page: ft.Page):
    page.title = "Gestionnaire d'Emploi du Temps"
    page.padding = 20
    page.scroll = "adaptive"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = ft.colors.LIGHT_BLUE_50

    # Styles de couleur pour l'interface
    BUTTON_COLOR = ft.colors.INDIGO_600
    BACKGROUND_COLOR = ft.colors.WHITE
    TEXT_COLOR = ft.colors.GREY_900

    # Fonction pour créer le menu horizontal
    def create_horizontal_menu():
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Column(
                        controls=[
                            ft.IconButton(
                                icon=ft.icons.CHECKLIST,
                                tooltip="Tâches",
                                on_click=lambda e: task_tab(),
                                icon_size=24,
                                style=ft.ButtonStyle(color=ft.colors.BLUE_500)
                            ),
                            ft.Text("Tâches", size=12, color=ft.colors.BLACK54)
                        ],
                        alignment=ft.MainAxisAlignment.CENTER
                    ),
                    ft.Column(
                        controls=[
                            ft.IconButton(
                                icon=ft.icons.NOTE,
                                tooltip="Notes",
                                on_click=lambda e: notes_tab(),
                                icon_size=24,
                                style=ft.ButtonStyle(color=ft.colors.BLUE_500)
                            ),
                            ft.Text("Notes", size=12, color=ft.colors.BLACK54)
                        ],
                        alignment=ft.MainAxisAlignment.CENTER
                    ),
                    ft.Column(
                        controls=[
                            ft.IconButton(
                                icon=ft.icons.SCHEDULE,
                                tooltip="Planning",
                                on_click=lambda e: schedule_tab(),
                                icon_size=24,
                                style=ft.ButtonStyle(color=ft.colors.BLUE_500)
                            ),
                            ft.Text("Planning", size=12, color=ft.colors.BLACK54)
                        ],
                        alignment=ft.MainAxisAlignment.CENTER
                    ),
                    ft.Column(
                        controls=[
                            ft.IconButton(
                                icon=ft.icons.CALENDAR_MONTH,
                                tooltip="Calendrier",
                                on_click=lambda e: calendar_tab(),
                                icon_size=24,
                                style=ft.ButtonStyle(color=ft.colors.BLUE_500)
                            ),
                            ft.Text("Calendrier", size=12, color=ft.colors.BLACK54)
                        ],
                        alignment=ft.MainAxisAlignment.CENTER
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_EVENLY,
                spacing=40
            ),
            padding=ft.padding.all(10),
            bgcolor=ft.colors.WHITE,
            border=ft.border.all(1, ft.colors.BLACK12),
            border_radius=ft.border_radius.all(8),
            shadow=ft.BoxShadow(spread_radius=2, blur_radius=4, color=ft.colors.BLACK12)
        )

    # Fonction pour afficher un contenu avec le menu horizontal
    def show_with_menu(content):
        page.controls.clear()
        page.controls.append(create_horizontal_menu())
        page.controls.append(ft.Divider(height=10, color=ft.colors.TRANSPARENT))
        page.controls.append(content)
        page.update()
    # Fonction pour sauvegarder les données de manière sécurisée
    def save_data(file="data.json"):
        try:
            with open(file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            page.snack_bar = ft.SnackBar(ft.Text(f"Erreur de sauvegarde des données : {e}"))
            page.snack_bar.open = True
            page.update()

    # Fonction pour charger les données avec gestion des erreurs
    def load_data(file="data.json"):
        if os.path.exists(file):
            try:
                with open(file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                page.snack_bar = ft.SnackBar(ft.Text(f"Erreur de chargement des données : {e}"))
                page.snack_bar.open = True
                page.update()
        return {"task_lists": {}, "notes": {}, "schedule": {}, "events": []}
        # Initialisation des données
    data = load_data("data.json")
    # Fonction pour gérer les notifications avec une meilleure gestion des ressources
    def notification_checker():
        try:
            while True:
                now = datetime.now()
                check_notifications(now)
                tm.sleep(60)
        except Exception as e:
            page.overlay.append(ft.Text(f"Erreur dans le système de notifications : {e}"))
            page.open = True
            page.update()

    # Fonction pour vérifier les notifications des tâches et événements
    def check_notifications(now):
        try:
            # Vérification des tâches
            for task_list in data["task_lists"].values():
                for task in task_list["tasks"]:
                    check_task_notification(task, now)
            # Vérification des événements
            for event in data["events"]:
                check_event_notification(event, now)
        except Exception as e:
            page.snack_bar = ft.SnackBar(ft.Text(f"Erreur lors de la vérification des notifications : {e}"))
            page.snack_bar.open = True
            page.update()

    # Fonction pour vérifier et envoyer une notification pour une tâche
    def check_task_notification(task, now):
        try:
            task_time = datetime.strptime(task["time"], "%Y-%m-%d %H:%M")
            if task_time <= now and not task.get("notified", False):
                page.snack_bar = ft.SnackBar(ft.Text(f"Rappel Tâche: {task['title']}"))
                page.snack_bar.open = True
                task["notified"] = True
                save_data()
        except ValueError:
            return  # Si le format de date/heure est incorrect, on l'ignore, mais on pourrait aussi alerter l'utilisateur

    # Fonction pour vérifier et envoyer une notification pour un événement
    def check_event_notification(event, now):
        try:
            event_date = datetime.strptime(event["date"], "%Y-%m-%d")
            if event_date.date() == now.date() and not event.get("notified", False):
                page.snack_bar = ft.SnackBar(ft.Text(f"Rappel Événement: {event['title']}"))
                page.snack_bar.open = True
                event["notified"] = True
                save_data()
        except ValueError:
            return  # Gestion du mauvais format de date

    # Démarrer le thread des notifications
    threading.Thread(target=notification_checker, daemon=True).start()

    # Fonctionnalité Liste de tâches
    def task_tab():
        task_lists_view = ft.Column(expand=True, spacing=10,scroll=ft.ScrollMode.AUTO)
        new_list_title = ft.TextField(label="Titre de la nouvelle liste", expand=True, border_radius=8, border_color=ft.colors.BLUE_200)
        add_list_button = ft.ElevatedButton(text="Ajouter une liste de tâches", on_click=lambda e: show_new_list_fields(), bgcolor=ft.colors.BLUE, color=ft.colors.WHITE)

        def show_new_list_fields():
            new_list_title.value = ""
            dialog = ft.AlertDialog(
                title=ft.Text("Nouvelle Liste de Tâches", size=18, weight="bold"),
                content=ft.Column([new_list_title]),
                actions=[
                    ft.TextButton("Annuler", on_click=lambda e: close_dialog(), style=ft.ButtonStyle(color=ft.colors.RED)),
                    ft.TextButton("Ajouter", on_click=lambda e: add_task_list(), style=ft.ButtonStyle(bgcolor=ft.colors.BLUE, color=ft.colors.WHITE))
                ]
            )
            page.dialog = dialog
            dialog.open = True
            page.update()

        def close_dialog():
            page.dialog.open = False
            page.update()

        def add_task_list():
            title = new_list_title.value.strip()
            if not title:
                page.snack_bar = ft.SnackBar(ft.Text("Le titre de la liste ne peut pas être vide"))
                page.snack_bar.open = True
                page.update()
                return
            if title in data["task_lists"]:
                page.snack_bar = ft.SnackBar(ft.Text("Une liste avec ce titre existe déjà"))
                page.snack_bar.open = True
                page.update()
                return
            data["task_lists"][title] = {"tasks": []}
            save_data()
            refresh_task_lists()
            close_dialog()

        def refresh_task_lists():
            task_lists_view.controls.clear()
            for title in data["task_lists"]:
                task_lists_view.controls.append(create_task_list_tile(title))
                print(title)
            page.update()

        def create_task_list_tile(title):
            return ft.ListTile(
                    title=ft.Text(title, size=16, weight="bold", color=ft.colors.BLACK, max_lines=1),
                    on_click=lambda e: open_task_list(title),
                    trailing=ft.IconButton(
                        icon=ft.icons.DELETE,
                        on_click=lambda e, t=title: delete_task_list(t),
                        icon_size=18,
                        bgcolor=ft.colors.RED

                    )

                )

        

        def delete_task_list(title):
            del data["task_lists"][title]
            save_data()
            refresh_task_lists()

        def open_task_list(title):
            task_list = data["task_lists"][title]
            task_view = ft.Column(expand=True, spacing=10,scroll=ft.ScrollMode.AUTO)
            task_title = ft.TextField(label="Titre de la tâche", expand=True, border_radius=8, border_color=ft.colors.BLUE_200)
            task_time = ft.TextField(label="Heure (YYYY-MM-DD HH:MM)", expand=True, border_radius=8, border_color=ft.colors.BLUE_200)

            def refresh_tasks():
                task_view.controls.clear()
                for task in task_list["tasks"]:
                    task_view.controls.append(create_task_tile(task, task_list))
                page.update()

            def create_task_tile(task, task_list):
                return ft.ListTile(
                    leading=ft.Checkbox(value=task.get("completed", False), on_change=lambda e: toggle_task_completion(task)),
                    title=ft.Text(task["title"], size=14),
                    subtitle=ft.Text(task["time"], size=12),
                    trailing=ft.IconButton(icon=ft.icons.DELETE, on_click=lambda e, t=task: delete_task(task, task_list), icon_size=18, bgcolor=ft.colors.RED),

                )

            def add_task(e):
                title = task_title.value.strip()
                time = task_time.value.strip()

                # Validation stricte des données d'entrée
                if not title or not time:
                    page.snack_bar = ft.SnackBar(ft.Text("Le titre et l'heure ne peuvent pas être vides"))
                    page.snack_bar.open = True
                    page.update()
                    return

                task = {"title": title, "time": time, "notified": False, "completed": False}
                task_list["tasks"].append(task)
                save_data()
                refresh_tasks()
                task_title.value = ""
                task_time.value = ""
                page.update()

            def delete_task(task, task_list):
                task_list["tasks"].remove(task)
                save_data()
                refresh_tasks()

            def toggle_task_completion(task):
                task["completed"] = not task.get("completed", False)
                save_data()
                refresh_tasks()

            page.views.append(
                ft.View(
                    "/tasks",
                    [
                        ft.AppBar(
                            title=ft.Text(f"Liste: {title}", size=20, weight="bold"),
                            leading=ft.IconButton(icon=ft.icons.ARROW_BACK, on_click=lambda e: go_back())
                        ),
                        ft.Column([
                            ft.Row([task_title, task_time]),
                            ft.ElevatedButton(text="Ajouter une tâche", on_click=add_task, bgcolor=ft.colors.BLUE, color=ft.colors.WHITE),
                            ft.Divider(),
                            ft.Text("Tâches:", style="headlineSmall", size=18),
                            task_view
                        ], expand=True, spacing=10)
                    ],scroll=ft.ScrollMode.AUTO,spacing=20
                )
            )
            refresh_tasks()
            page.go("/tasks")

        def go_back():
            if len(page.views) > 1:
                page.views.pop()
                page.go(page.views[-1].route)

        refresh_task_lists()

        show_with_menu(ft.Column([
            ft.Divider(),
            add_list_button,
            ft.Text("Listes de tâches:", style="headlineSmall", size=18),
            task_lists_view
        ], expand=True, scroll=ft.ScrollMode.AUTO,spacing=20))

    # Fonctionnalité Bloc-notes
    def notes_tab():
        notes_list_view = ft.Column(expand=True, spacing=10,scroll=ft.ScrollMode.AUTO)
        new_note_title = ft.TextField(label="Titre de la nouvelle note", expand=True, border_radius=8, border_color=ft.colors.BLUE_200)
        add_note_button = ft.ElevatedButton(text="Ajouter une note", on_click=lambda e: show_new_note_fields(), bgcolor=ft.colors.BLUE, color=ft.colors.WHITE)

        def show_new_note_fields():
            new_note_title.value = ""
            dialog = ft.AlertDialog(
                title=ft.Text("Nouvelle Note", size=18, weight="bold"),
                content=ft.Column([new_note_title]),
                actions=[
                    ft.TextButton("Annuler", on_click=lambda e: close_dialog(), style=ft.ButtonStyle(color=ft.colors.RED)),
                    ft.TextButton("Ajouter", on_click=lambda e: add_note(), style=ft.ButtonStyle(bgcolor=ft.colors.BLUE, color=ft.colors.WHITE))
                ]
            )
            page.dialog = dialog
            dialog.open = True
            page.update()

        def close_dialog():
            page.dialog.open = False
            page.update()

        def add_note():
            title = new_note_title.value.strip()
            if title:
                if title in data["notes"]:
                    page.snack_bar = ft.SnackBar(ft.Text("Une note avec ce titre existe déjà"))
                    page.snack_bar.open = True
                    page.update()
                else:
                    data["notes"][title] = ""
                    save_data()
                    refresh_notes_list()
                    close_dialog()
            else:
                page.snack_bar = ft.SnackBar(ft.Text("Le titre ne peut pas être vide"))
                page.snack_bar.open = True
                page.update()

        def refresh_notes_list():
            notes_list_view.controls.clear()
            for title in data["notes"]:
                notes_list_view.controls.append(create_note_tile(title))
            page.update()

        def create_note_tile(title):
            return ft.Row(
                [
                    ft.Container(
                        content=ft.Text(title, size=16, weight="bold", color=ft.colors.BLACK, max_lines=1),
                        on_click=lambda e: open_note(title),  # Appel de la fonction d'ouverture au clic
                        padding=ft.padding.all(10),
                        expand=True  # Permet au texte de s'étendre dans le Row
                    ),
                    ft.IconButton(
                        icon=ft.icons.DELETE,
                        on_click=lambda e: delete_note(title),
                        icon_size=18,
                        bgcolor=ft.colors.RED

                    )
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                spacing=10,scroll=ft.ScrollMode.AUTO
            )

        def delete_note(title):
            del data["notes"][title]
            save_data()
            refresh_notes_list()

        def open_note(title):
            note_content = ft.TextField(
                label="Contenu de la note",
                multiline=True,
                expand=True,
                value=data["notes"][title],
                keyboard_type=ft.KeyboardType.TEXT,
                border_radius=8,
                border_color=ft.colors.BLUE_200,
                height=300
            )

            def save_note_content(e):
                data["notes"][title] = note_content.value
                save_data()
                page.snack_bar = ft.SnackBar(ft.Text("Note sauvegardée"))
                page.snack_bar.open = True
                page.update()

            page.views.append(
                ft.View(
                    "/note",
                    [
                        ft.AppBar(
                            title=ft.Text(f"Note: {title}", size=20, weight="bold"),
                            leading=ft.IconButton(icon=ft.icons.ARROW_BACK, on_click=lambda e: go_back())
                        ),
                        ft.Column([
                            note_content,
                            ft.ElevatedButton(text="Sauvegarder la note", on_click=save_note_content, bgcolor=ft.colors.BLUE, color=ft.colors.WHITE)
                        ], expand=True, scroll=ft.ScrollMode.AUTO,spacing=10)
                    ]
                )
            )
            page.go("/note")

        def go_back():
            if len(page.views) > 1:
                page.views.pop()
                page.go(page.views[-1].route)

        refresh_notes_list()

        show_with_menu(ft.Column([
            ft.Divider(),
            add_note_button,
            ft.Text("Notes:", style="headlineSmall", size=18),
            notes_list_view
        ], expand=True, scroll=ft.ScrollMode.AUTO, spacing=20))

    # Fonctionnalité Emploi du Temps
    def schedule_tab():
        schedule_manager = ScheduleManager()

        def time_str_to_time(time_str: str) -> Optional[time]:
            """Convertit des chaînes comme '6h', '6h30', '6h00', '7', '7h' en objet time."""
            time_str = time_str.strip()
            time_str = time_str.replace('h', ':')
            if time_str.endswith(':'):
                time_str += '00'
            try:
                return datetime.strptime(time_str, '%H:%M').time()
            except ValueError:
                try:
                    return datetime.strptime(time_str, '%H').time()
                except ValueError:
                    return None

        def refresh_schedule():
            """Rafraîchit l'affichage de l'emploi du temps."""
            time_slots = schedule_manager.time_slots
            days = list(schedule_manager.schedule.keys())

            # Grille principale pour l'emploi du temps
            grid = ft.Column(spacing=2, expand=True)

            # Ligne des en-têtes (jours)
            header_row = ft.Row(
                [
                    ft.Container(
                        content=ft.Text("Heures", weight="bold", size=14, text_align="center"),
                        bgcolor=ft.colors.BLUE_GREY_100,
                        padding=10,
                        expand=True,
                        border=ft.border.all(1, ft.colors.BLACK12),
                    )
                ]
                + [
                    ft.Container(
                        content=ft.Text(day.capitalize(), weight="bold", size=14, text_align="center"),
                        bgcolor=ft.colors.BLUE_GREY_100,
                        padding=10,
                        expand=True,
                        border=ft.border.all(1, ft.colors.BLACK12),
                    )
                    for day in days
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            )

            # Lignes horaires et colonnes des contenus
            for time_slot in time_slots:
                row = ft.Row(
                    [
                        # Colonne des heures
                        ft.Container(
                            content=ft.Text(time_slot, weight="bold", size=12, text_align="center"),
                            bgcolor=ft.colors.LIGHT_GREEN_50,
                            padding=10,
                            expand=True,
                            border=ft.border.all(1, ft.colors.BLACK12),
                        )
                    ]
                    + [
                        # Colonnes pour chaque jour
                        ft.Container(
                            content=get_cell_content(day, time_slot),
                            bgcolor=ft.colors.WHITE,
                            padding=10,
                            expand=True,
                            border=ft.border.all(1, ft.colors.BLACK12),
                        )
                        for day in days
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                )
                grid.controls.append(row)

            # Mise à jour de la vue avec l'emploi du temps
            schedule_view.content = ft.Column(
                [
                    ft.Text("Emploi du temps", size=24, weight="bold", text_align="center"),
                    header_row,
                    ft.Divider(height=1, thickness=1, color=ft.colors.BLACK12),
                    grid,
                ],
                expand=True,
            )
            page.update()

        def get_cell_content(day: str, time_slot_str: str) -> ft.Text:
            """Génère le contenu d'une cellule de l'emploi du temps."""
            start_str, end_str = time_slot_str.split('-')
            slot_start_time = time_str_to_time(start_str)
            slot_end_time = time_str_to_time(end_str.replace('h', ''))

            if slot_start_time is None or slot_end_time is None:
                return ft.Text("Erreur", color=ft.colors.RED)

            day_upper = day.upper()
            for slot in schedule_manager.schedule[day_upper]:
                if slot.start_time <= slot_start_time < slot.end_time:
                    return ft.Text(
                        slot.course,
                        weight="bold",
                        color=ft.colors.BLACK,
                        size=12,
                    )

            return ft.Text("")  # Cellule vide si aucun contenu n'est trouvé

        def show_add_event_dialog():
            """Affiche un formulaire pour ajouter un événement."""
            day_dropdown = ft.Dropdown(
                label="Jour",
                options=[ft.dropdown.Option(day.capitalize()) for day in schedule_manager.schedule.keys()],
                width=200
            )
            start_field = ft.TextField(label="Heure de début (ex: 6h)", width=200)
            end_field = ft.TextField(label="Heure de fin (ex: 7h)", width=200)
            course_field = ft.TextField(label="Cours", width=400)
            temp_checkbox = ft.Checkbox(label="Temporaire", value=False)
            error_text = ft.Text("", color=ft.colors.RED)

            def add_event(e):
                """Ajoute un nouvel événement."""
                if not all([
                    day_dropdown.value,
                    start_field.value,
                    end_field.value,
                    course_field.value
                ]):
                    error_text.value = "Tous les champs sont obligatoires."
                    page.update()
                    return

                start = time_str_to_time(start_field.value)
                end = time_str_to_time(end_field.value)

                if start is None or end is None:
                    error_text.value = "Format d'heure invalide (utilisez '6h' ou '6h30')."
                    page.update()
                    return

                day_upper = day_dropdown.value.upper()

                if schedule_manager.add_time_slot(
                        day_upper, start, end, course_field.value, temp_checkbox.value
                ):
                    error_text.value = ""
                    page.dialog.open = False
                    refresh_schedule()
                else:
                    error_text.value = "Horaire invalide ou conflit détecté."
                    page.update()

            add_button = ft.ElevatedButton("Ajouter", on_click=add_event, bgcolor=ft.colors.BLUE, color=ft.colors.WHITE)

            page.dialog = ft.AlertDialog(
                title=ft.Text("Ajouter un événement"),
                content=ft.Column([
                    day_dropdown,
                    start_field,
                    end_field,
                    course_field,
                    temp_checkbox,
                    error_text
                ]),
                actions=[
                    ft.TextButton("Annuler", on_click=lambda e: close_dialog()),
                    add_button
                ]
            )
            page.dialog.open = True
            page.update()

        def close_dialog():
            """Ferme le formulaire."""
            page.dialog.open = False
            page.update()

        # Conteneur principal pour l'emploi du temps
        schedule_view = ft.Container(content=ft.Column([]), padding=10, expand=True)

        # Bouton "+" pour ajouter un événement
        add_event_button = ft.FloatingActionButton(
            icon=ft.icons.ADD,
            bgcolor=ft.colors.BLUE,
            on_click=lambda e: show_add_event_dialog(),
            tooltip="Ajouter un événement"
        )

        # Rafraîchir l'emploi du temps pour afficher les données
        refresh_schedule()

        # Affichage final avec le bouton "+" fixe en bas
        show_with_menu(
            ft.Stack(
                [
                    schedule_view,
                    ft.Container(
                        content=add_event_button,
                        alignment=ft.alignment.bottom_right,
                        margin=ft.margin.all(20),
                    ),
                ],
                expand=True,
            )
        )

        # Créer et retourner l'onglet


    # Fonctionnalité Calendrier améliorée (type Google Agenda)
    def calendar_tab():
        now = datetime.now()
        current_year = now.year
        current_month = now.month

        selected_date_text = ft.Text("Sélectionnez une date sur le calendrier", size=16)
        event_list_view = ft.Column()

        def generate_calendar(year, month):
            weekdays = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]

            first_day = date(year, month, 1)
            first_weekday = (first_day.weekday()) % 7

            if month == 12:
                next_month = date(year + 1, 1, 1)
            else:
                next_month = date(year, month + 1, 1)
            days_in_month = (next_month -timedelta(days=1)).day

            calendar = ft.Column(spacing=5, expand=True)

            header = ft.Row(
                [ft.Container(
                    ft.Text(day_name, weight="bold", size=16),
                    alignment=ft.alignment.center,
                    expand=True
                ) for day_name in weekdays],
                spacing=5
            )
            calendar.controls.append(header)

            week = []
            for _ in range(first_weekday):
                week.append(ft.Container(expand=True))

            for day in range(1, days_in_month + 1):
                date_str = f"{year}-{month:02d}-{day:02d}"
                events_today = [event for event in data["events"] if event["date"] == date_str]
                day_container = ft.Container(
                    content=ft.Text(str(day), size=14),
                    alignment=ft.alignment.center,
                    bgcolor=ft.colors.LIGHT_BLUE_100 if events_today else ft.colors.TRANSPARENT,
                    on_click=lambda e, d=date_str: select_date(d),
                    expand=True,
                    border=ft.border.all(1, ft.colors.BLACK12),
                    padding=10,
                    border_radius=ft.border_radius.all(8)
                )
                week.append(day_container)
                if len(week) == 7:
                    calendar.controls.append(ft.Row(week, spacing=5))
                    week = []
            if week:
                while len(week) < 7:
                    week.append(ft.Container(expand=True))
                calendar.controls.append(ft.Row(week, spacing=5))

            return calendar

        def select_date(selected_date):
            selected_date_text.value = f"Date sélectionnée : {selected_date}"
            refresh_events(selected_date)
            show_event_dialog(selected_date)
            page.update()

        def refresh_events(selected_date):
            event_list_view.controls.clear()
            for event in data["events"]:
                if event["date"] == selected_date:
                    current_event = event

                    def make_delete_handler(ev):
                        return lambda e: delete_event(ev, selected_date)

                    event_list_view.controls.append(
                        ft.ListTile(
                            title=ft.Text(event['title']),
                            trailing=ft.IconButton(
                                icon=ft.icons.DELETE,
                                on_click=make_delete_handler(current_event)
                            )
                        )
                    )
            page.update()

        def delete_event(event, selected_date):
            data["events"].remove(event)
            refresh_events(selected_date)
            refresh_calendar()

        def show_event_dialog(selected_date):
            event_title_field = ft.TextField(label="Titre de l'événement", expand=True)
            event_time_field = ft.TextField(label="Heure (HH:MM)", expand=True)
            event_description_field = ft.TextField(label="Description", multiline=True, expand=True)

            def add_event():
                title = event_title_field.value.strip()
                time = event_time_field.value.strip()
                description = event_description_field.value.strip()
                if title and time:
                    event = {
                        "title": title,
                        "date": selected_date,
                        "time": time,
                        "description": description
                    }
                    data["events"].append(event)
                    refresh_events(selected_date)
                    refresh_calendar()
                    close_dialog()
                else:
                    page.snack_bar = ft.SnackBar(ft.Text("Le titre et l'heure ne peuvent pas être vides"))
                    page.snack_bar.open = True
                    page.update()

            def close_dialog():
                page.dialog.open = False
                page.update()

            dialog = ft.AlertDialog(
                title=ft.Text(f"Ajouter un événement pour le {selected_date}"),
                content=ft.Column([event_title_field, event_time_field, event_description_field]),
                actions=[
                    ft.TextButton("Annuler", on_click=lambda e: close_dialog()),
                    ft.TextButton("Ajouter", on_click=lambda e: add_event())
                ]
            )
            page.dialog = dialog
            dialog.open = True
            page.update()

        def refresh_calendar():
            calendar_container.content = generate_calendar(current_year, current_month)
            update_month_label()
            page.update()

        calendar_container = ft.Container(expand=True)

        def prev_month(e):
            nonlocal current_month, current_year
            if current_month == 1:
                current_month = 12
                current_year -= 1
            else:
                current_month -= 1
            refresh_calendar()

        def next_month(e):
            nonlocal current_month, current_year
            if current_month == 12:
                current_month = 1
                current_year += 1
            else:
                current_month += 1
            refresh_calendar()

        month_label = ft.Text("", style="headlineMedium", weight="bold", size=24)

        def update_month_label():
            month_name = date(current_year, current_month, 1).strftime('%B %Y')
            month_label.value = month_name.capitalize()
            page.update()

        month_navigation = ft.Row(
            [
                ft.Container(
                    content=ft.IconButton(icon=ft.icons.ARROW_BACK, on_click=prev_month, icon_size=20),
                    bgcolor=ft.colors.BLUE_200,
                    border_radius=ft.border_radius.all(12),
                    padding=8
                ),
                ft.Icon(name=ft.icons.CALENDAR_MONTH, size=24, color=ft.colors.BLUE_500),
                month_label,
                ft.Container(
                    content=ft.IconButton(icon=ft.icons.ARROW_FORWARD, on_click=next_month, icon_size=20),
                    bgcolor=ft.colors.BLUE_200,
                    border_radius=ft.border_radius.all(12),
                    padding=8
                )
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10
        )

        refresh_calendar()

        show_with_menu(ft.Column(
            [
                month_navigation,
                calendar_container,
                selected_date_text,
                ft.Divider(),
                ft.Text("Événements pour la date sélectionnée :", style="headlineSmall", size=18),
                event_list_view
            ],
            expand=True,
            spacing=20
        ))

    show_with_menu(ft.Text("Sélectionnez une fonctionnalité dans le menu déroulant.", color=TEXT_COLOR, text_align="center"))
ft.app(main)
