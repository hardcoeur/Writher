import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio, Pango, Gdk
import subprocess
import re

class TextEditor(Gtk.Window):

    def __init__(self):
        Gtk.Window.__init__(self, title="Writher")
        self.set_default_size(800, 600)

        # Box layout
        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(self.box)

        # HeaderBar
        self.header_bar = Gtk.HeaderBar()
        self.header_bar.set_show_close_button(True)
        self.header_bar.props.title = "Writher"
        self.set_titlebar(self.header_bar)

        # Open button with arrow
        self.open_button = Gtk.MenuButton.new()
        self.open_button.set_label('Open \u25BC')
        self.header_bar.pack_start(self.open_button)

        # Popover menu with open and save options
        self.menu = Gio.Menu()
        self.menu.append("Open", "app.open")
        self.menu.append("Save", "app.save")
        self.open_button.set_menu_model(self.menu)
        
        # Font and font-size selection list
        self.font_combo = Gtk.ComboBoxText()

        # Get available font families using fc-list command
        output = subprocess.check_output(["fc-list", ":lang=en", "--format=%{family[0]}\n"])
        font_families = output.decode("utf-8").splitlines()

        # Remove duplicates and sort font families
        unique_font_families = sorted(set(font_families))

        # Populate the font combo box with the font families
        for idx, font_family in enumerate(unique_font_families):
            self.font_combo.insert(idx, font_family, font_family)

        self.font_combo.set_active(0)

        self.font_size_combo = Gtk.ComboBoxText()
        self.font_size_combo.insert(0, "8", "8")
        self.font_size_combo.insert(1, "10", "10")
        self.font_size_combo.insert(2, "12", "12")
        self.font_size_combo.insert(3, "14", "14")
        self.font_size_combo.insert(4, "16", "16")
        self.font_size_combo.insert(5, "18", "18")
        self.font_size_combo.insert(6, "20", "20")
        self.font_size_combo.insert(7, "22", "22")
        self.font_size_combo.insert(8, "24", "24")
        self.font_size_combo.set_active(4)

        self.font_combo.connect("changed", self.on_font_changed)
        self.font_size_combo.connect("changed", self.on_font_size_changed)

        font_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        font_box.set_margin_start(4)

        # Add the font combo box and font size combo box to the font_box
        font_box.pack_start(self.font_combo, False, False, 0)
        font_box.pack_start(self.font_size_combo, False, False, 0)

        # Add the font_box to the right of the "Open" button in the headerbar
        self.header_bar.pack_end(font_box)

        # TextView
        self.text_view = Gtk.TextView()
        self.text_view.set_margin_start(0)
        self.text_view.set_margin_end(0)
        self.text_view.set_margin_top(0)
        self.text_view.set_margin_bottom(0)
        self.text_view.set_left_margin(80)
        self.text_view.set_right_margin(80)
        self.text_view.set_top_margin(40)
        self.text_view.set_bottom_margin(20)

        # Connect the changed signal to update the title
        self.text_view.get_buffer().connect("changed", self.on_text_buffer_changed)

        # Set word wrapping
        self.text_view.set_wrap_mode(Gtk.WrapMode.WORD)
        self.text_buffer = self.text_view.get_buffer()

         # ScrolledWindow
        self.scrolled_window = Gtk.ScrolledWindow()
        self.scrolled_window.add(self.text_view)

        # Utility pane
        self.utility_pane = Gtk.ListBox()
        self.utility_pane.set_selection_mode(Gtk.SelectionMode.NONE)
        css = b"""
            list { background-color: inherit; }
            """
        self.apply_css(self.utility_pane, css)

        self.utility_pane.set_vexpand(False)
        self.utility_pane.set_valign(Gtk.Align.START)
        self.utility_pane.set_selection_mode(Gtk.SelectionMode.NONE)
        self.utility_pane.set_margin_top(20)
        self.utility_pane.set_margin_start(20)
        self.utility_pane.set_margin_end(20)

        width, _ = self.get_size()
        utility_pane_width = int(width * 0.11)
        self.utility_pane.set_size_request(utility_pane_width, -1)

        self.utility_labels = {
            "Words": Gtk.Label.new("0"),
            "Characters": Gtk.Label.new("0"),
            "Sentences": Gtk.Label.new("0"),
            "Paragraphs": Gtk.Label.new("0"),
            "Reading time": Gtk.Label.new("0"),
        }

        for label in self.utility_labels.values():
            label.set_use_markup(True)
            attr_list = Pango.AttrList()
            attr_list.insert(Pango.attr_weight_new(Pango.Weight.BOLD))
            label.set_attributes(attr_list)


        for key, label in self.utility_labels.items():
            row = Gtk.ListBoxRow()
            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=30)
            row.add(hbox)
            label_key = Gtk.Label.new(key + ":")
            hbox.pack_start(label_key, False, False, 0)
            hbox.pack_start(label, False, False, 0)
            self.utility_pane.add(row)

        # Main layout
        self.main_layout = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.main_layout.pack_start(self.utility_pane, False, False, 0)
        self.main_layout.pack_start(self.scrolled_window, True, True, 0)
        self.box.pack_start(self.main_layout, True, True, 0)

        # Open and save actions
        self.application = Gio.Application.get_default()
        self.open_action = Gio.SimpleAction.new("open", None)
        self.open_action.connect("activate", self.open_file)
        self.application.add_action(self.open_action)

        self.save_action = Gio.SimpleAction.new("save", None)
        self.save_action.connect("activate", self.save_file)
        self.application.add_action(self.save_action)
        
        # Connect the delete-event signal to the confirm_close function
        self.connect("delete-event", self.confirm_close)

        # Connect the window-state-event signal to the on_window_state_changed function
        self.connect("window-state-event", self.on_window_state_changed)

        # Connect the size-allocate signal to the on_size_allocate function
        self.connect("size-allocate", self.on_size_allocate)
    
    def apply_css(self, widget, css):
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(css)

        context = widget.get_style_context()
        context.add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        if isinstance(widget, Gtk.Container):
            for child in widget.get_children():
                self.apply_css(child, css)

    def update_title(self):
        text_buffer = self.text_view.get_buffer()
        if hasattr(self, 'file_path'):
            file_name = self.file_path.split('/')[-1]
        else:
            start, end = text_buffer.get_bounds()
            content = text_buffer.get_text(start, end, True)
            sentences = content.split('.')
            file_name = ' '.join(sentences[:3]) + "..."
        self.header_bar.set_title(f"Writher - {file_name}")

    def on_text_buffer_changed(self, text_buffer):
        self.update_title()

    def open_file(self, action, param):
        file_chooser = Gtk.FileChooserDialog(
            title="Open File",
            parent=self,
            action=Gtk.FileChooserAction.OPEN,
            buttons=(
                Gtk.STOCK_CANCEL,
                Gtk.ResponseType.CANCEL,
                Gtk.STOCK_OPEN,
                Gtk.ResponseType.OK,
            ),
        )

        response = file_chooser.run()
        if response == Gtk.ResponseType.OK:
            self.file_path = file_chooser.get_filename()
            with open(self.file_path, "r") as f:
                content = f.read()
                self.text_view.get_buffer().set_text(content)
            self.update_title()
        file_chooser.destroy()

    def save_file(self, action, param):
        file_chooser = Gtk.FileChooserDialog(
            title="Save File",
            parent=self,
            action=Gtk.FileChooserAction.SAVE,
            buttons=(
                Gtk.STOCK_CANCEL,
                Gtk.ResponseType.CANCEL,
                Gtk.STOCK_SAVE,
                Gtk.ResponseType.OK,
            ),
        )

        response = file_chooser.run()
        if response == Gtk.ResponseType.OK:
            self.file_path = file_chooser.get_filename()
            text_buffer = self.text_view.get_buffer()
            start, end = text_buffer.get_bounds()
            content = text_buffer.get_text(start, end, True)
            with open(self.file_path, "w") as f:
                f.write(content)
            self.update_title()
        file_chooser.destroy()

    def on_font_changed(self, combo):
        font_name = combo.get_active_text()
        font_desc = Pango.FontDescription.from_string(font_name + " " + str(self.font_size_combo.get_active_text()))
        self.text_view.modify_font(font_desc)

    def on_font_size_changed(self, combo):
        font_size = int(combo.get_active_text())
        font_desc = Pango.FontDescription.from_string(self.font_combo.get_active_text() + " " + str(font_size))
        self.text_view.modify_font(font_desc)
    
    def unsaved_changes(self):
        text_buffer = self.text_view.get_buffer()
        return text_buffer.get_modified()

    def unsaved_changes(self):
        text_buffer = self.text_view.get_buffer()
        return text_buffer.get_modified()

    def confirm_close(self, widget, event=None):
        if self.text_buffer.get_modified():
            dialog = Gtk.MessageDialog(
                transient_for=self,
                flags=0,
                message_type=Gtk.MessageType.QUESTION,
                buttons=Gtk.ButtonsType.YES_NO,
                text="Unsaved changes detected",
            )
            dialog.format_secondary_text(
                "You have unsaved changes. If you close the application now, your changes will be lost. Do you want to save your changes before closing?"
            )
            response = dialog.run()

            if response == Gtk.ResponseType.YES:
                dialog.destroy()
                self.save_file(widget)
            elif response == Gtk.ResponseType.NO:
                dialog.destroy()
                return False
            else:
                dialog.destroy()
                return True
        return False

    def on_window_state_changed(self, widget, event):
        fullscreen = event.new_window_state & Gdk.WindowState.FULLSCREEN
        self.utility_pane.set_visible(not fullscreen)

    def on_size_allocate(self, widget, allocation):
        width, _ = self.get_size()
        utility_pane_width = int(width * 0.11)
        self.utility_pane.set_size_request(utility_pane_width, -1)

    def update_utility_pane(self):        
        text_buffer = self.text_view.get_buffer()
        start, end = text_buffer.get_bounds()
        content = text_buffer.get_text(start, end, True)

        words = len(re.findall(r'\b\w+\b', content))
        self.utility_labels["Words"].set_text(str(words))

        chars = len(content)
        self.utility_labels["Characters"].set_text(str(chars))

        sentences = len(re.findall(r'[.!?]\s', content)) + 1
        self.utility_labels["Sentences"].set_text(str(sentences))

        paragraphs = len(re.findall(r'\n\s*\n', content)) + 1
        self.utility_labels["Paragraphs"].set_text(str(paragraphs))

        reading_time = int(words / 200)  # Assuming 200 words per minute reading speed
        self.utility_labels["Reading time"].set_text(str(reading_time) + " min")

    # Add the update_utility_pane method call to the on_text_buffer_changed method
    def on_text_buffer_changed(self, text_buffer):
        self.update_title()
        self.update_utility_pane()

class TextEditorApplication(Gtk.Application):
    
    def __init__(self):
        super().__init__(application_id="org.monster.writher")
        self.window = None

    def do_activate(self):
        if not self.window:
            self.window = TextEditor()
            self.window.set_application(self)
            self.window.show_all()
            self.add_window(self.window)
        self.window.present()

    def do_startup(self):
        Gtk.Application.do_startup(self)
    
    def close_request(self):
        if self.window:
            self.window.confirm_close(None)
            self.quit()
    
    def do_delete_event(self, window, event):
        if self.window.confirm_close(None):
            self.window.destroy()
        return True

    def do_window_removed(self, window):
        if self.get_windows():
            self.quit()
    
    def do_shutdown(self):
        if self.window:
            self.window.destroy()
        Gtk.Application.do_shutdown(self)

if __name__ == "__main__":
    app = TextEditorApplication()
    app.run(None)
