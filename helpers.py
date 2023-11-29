import re
import os
import subprocess
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio, Pango, Gdk


def update_utility_pane(text_view, utility_labels):
    text_buffer = text_view.get_buffer()
    start, end = text_buffer.get_bounds()
    content = text_buffer.get_text(start, end, True)

    words = len(re.findall(r'\b\w+\b', content))
    utility_labels["Words"].set_text(str(words))

    chars = len(content)
    utility_labels["Characters"].set_text(str(chars))

    sentences = len(re.findall(r'[.!?]\s', content)) + 1
    utility_labels["Sentences"].set_text(str(sentences))

    paragraphs = len(re.findall(r'\n\s*\n', content)) + 1
    utility_labels["Paragraphs"].set_text(str(paragraphs))

    reading_time = int(words / 200)  # Assuming 200 words per minute reading speed
    utility_labels["Reading time"].set_text(str(reading_time) + " min")

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

def on_export_rtf(self, action, param):
    # Get the Markdown text
    markdown_text = self.text_view.get_buffer().get_text(
        self.text_view.get_buffer().get_start_iter(),
        self.text_view.get_buffer().get_end_iter(),
        False
    )

    # Convert the Markdown to RTF using pandoc command-line tool
    pandoc_cmd = ['pandoc', '-f', 'markdown', '-t', 'rtf', '-s']
    pandoc_process = subprocess.Popen(pandoc_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    rtf_content, _ = pandoc_process.communicate(input=markdown_text.encode('utf-8'))

    # Open the file chooser dialog to choose a file path to save the RTF file to
    file_chooser = Gtk.FileChooserDialog(
        title="Export to RTF",
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
        rtf_file_path = file_chooser.get_filename()
        # Save the RTF content to the selected file path
        if rtf_file_path is not None:
            with open(rtf_file_path, 'wb') as f:
                f.write(rtf_content)

            # Notify the user that the export is complete
            dialog = Gtk.MessageDialog(
                parent=self,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                text="Export complete"
            )
            dialog.run()
            dialog.destroy()

    file_chooser.destroy()

def on_export_pdf(self, action, param):
    # Get the Markdown text
    markdown_text = self.text_view.get_buffer().get_text(
        self.text_view.get_buffer().get_start_iter(),
        self.text_view.get_buffer().get_end_iter(),
        False
    )

    # Save the Markdown content to a temporary file
    with open('temp.md', 'w') as temp_md_file:
        temp_md_file.write(markdown_text)

    # Open the file chooser dialog to choose a file path to save the PDF file to
    file_chooser = Gtk.FileChooserDialog(
        title="Export to PDF",
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
        pdf_file_path = file_chooser.get_filename()
        # Convert the Markdown to PDF using pandoc command-line tool with the pdflatex engine
        pandoc_cmd = ['pandoc', '-f', 'markdown', '-t', 'pdf', '-s', '-o', pdf_file_path, 'temp.md', '--pdf-engine=pdflatex']
        subprocess.run(pandoc_cmd)

        # Notify the user that the export is complete
        dialog = Gtk.MessageDialog(
            parent=self,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="Export complete"
        )
        dialog.run()
        dialog.destroy()

    file_chooser.destroy()

    # Remove the temporary Markdown file
    os.remove('temp.md')

def on_font_changed(self, combo):
    font_name = combo.get_active_text()
    font_desc = Pango.FontDescription.from_string(font_name + " " + str(self.font_size_combo.get_active_text()))
    self.text_view.modify_font(font_desc)

def on_font_size_changed(self, combo):
    font_size = int(combo.get_active_text())
    font_desc = Pango.FontDescription.from_string(self.font_combo.get_active_text() + " " + str(font_size))
    self.text_view.modify_font(font_desc)

def unsaved_changes(text_buffer):
    return text_buffer.get_modified()

def confirm_close(window, text_buffer, widget, event=None):
    if unsaved_changes(text_buffer):
        dialog = Gtk.MessageDialog(
            transient_for=window,
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
            window.save_file(widget)
        elif response == Gtk.ResponseType.NO:
            dialog.destroy()
            return False
        else:
            dialog.destroy()
            return True
    return False