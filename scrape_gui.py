import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import os
import sys
from PIL import Image, ImageTk
import webbrowser
from tkinter import messagebox
from ttkthemes import ThemedTk
from dotenv import load_dotenv
load_dotenv()

# Import functions from the scrape.py file
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from scrape import process_article

# Material Design inspired colors
COLORS = {
    "background": "#FAFAFA",
    "card": "#FFFFFF",
    "text_primary": "#212121",
    "text_secondary": "#757575",
    "divider": "#E0E0E0",
    "primary": "#1976D2",
    "primary_dark": "#1565C0",
}

class MaterialButton(tk.Button):
    """Custom button with Material Design styling"""
    def __init__(self, master=None, **kwargs):
        self.default_bg = kwargs.get('background', COLORS['primary'])
        self.hover_bg = kwargs.get('activebackground', COLORS['primary_dark'])
        
        kwargs['background'] = self.default_bg
        kwargs['activebackground'] = self.hover_bg
        kwargs['foreground'] = 'white'
        kwargs['activeforeground'] = 'white'
        kwargs['relief'] = 'flat'
        kwargs['borderwidth'] = 0
        kwargs['padx'] = 16
        kwargs['pady'] = 8
        kwargs['font'] = ('Segoe UI', 10)
        
        super().__init__(master, **kwargs)
        
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
    
    def _on_enter(self, e):
        self['background'] = self.hover_bg
        
    def _on_leave(self, e):
        self['background'] = self.default_bg

class MaterialEntry(tk.Frame):
    """Custom entry field with Material Design styling"""
    def __init__(self, master=None, placeholder="", **kwargs):
        super().__init__(master, background=COLORS['background'], **kwargs)
        
        self.placeholder = placeholder
        self.placeholder_color = COLORS['text_secondary']
        self.default_fg = COLORS['text_primary']
        
        # Create the entry widget
        self.entry = tk.Entry(self, 
                             background=COLORS['card'],
                             foreground=self.placeholder_color,
                             insertbackground=COLORS['primary'],
                             relief='flat',
                             font=('Segoe UI', 11),
                             highlightthickness=1,
                             highlightbackground=COLORS['divider'],
                             highlightcolor=COLORS['primary'])
        
        # Place a bottom border
        self.border_frame = tk.Frame(self, background=COLORS['divider'], height=1)
        
        # Layout
        self.entry.pack(fill='x', expand=True, ipady=8)
        self.border_frame.pack(fill='x', expand=True)
        
        # Set placeholder
        self.entry.insert(0, self.placeholder)
        
        # Bind events
        self.entry.bind("<FocusIn>", self._on_focus_in)
        self.entry.bind("<FocusOut>", self._on_focus_out)
        
    def _on_focus_in(self, event):
        if self.entry.get() == self.placeholder:
            self.entry.delete(0, tk.END)
            self.entry.config(foreground=self.default_fg)
        self.border_frame.config(background=COLORS['primary'], height=2)
            
    def _on_focus_out(self, event):
        if not self.entry.get():
            self.entry.insert(0, self.placeholder)
            self.entry.config(foreground=self.placeholder_color)
        self.border_frame.config(background=COLORS['divider'], height=1)
    
    def get(self):
        """Get the entry text, returning empty string if it's the placeholder"""
        if self.entry.get() == self.placeholder:
            return ""
        return self.entry.get()
    
    def set(self, text):
        """Set the entry text"""
        self.entry.delete(0, tk.END)
        self.entry.insert(0, text)
        if text and text != self.placeholder:
            self.entry.config(foreground=self.default_fg)
        else:
            self.entry.config(foreground=self.placeholder_color)

class MaterialCard(tk.Frame):
    """Frame styled as a Material Design card"""
    def __init__(self, master=None, **kwargs):
        kwargs['background'] = COLORS['card']
        kwargs['highlightbackground'] = COLORS['divider']
        kwargs['highlightthickness'] = 1
        kwargs['padx'] = 16
        kwargs['pady'] = 16
        super().__init__(master, **kwargs)

class NewsScraperApp(ThemedTk):
    """Main application window"""
    def __init__(self):
        super().__init__(theme="arc")  
        
        self.title("News Article Scraper")
        self.geometry("900x700")
        self.minsize(600, 400)  
        self.configure(background=COLORS['background'])
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        self._create_widgets()
        
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
        
        self.bind('<Configure>', self._on_resize)
        
        self.api_key = os.getenv('HUGGINGFACE_API_KEY')
        if not self.api_key:
            messagebox.showerror("API Key Error", "HUGGINGFACE_API_KEY not set in .env or environment.")
            self.destroy()
            return
    
    def _create_widgets(self):
        """Create all the UI widgets using ttk for full theme support"""
        # Header
        header_frame = ttk.Frame(self, padding=(16, 16, 16, 16))
        header_frame.pack(fill='x')
        header_label = ttk.Label(
            header_frame,
            text="News Article Scraper & Summarizer",
            font=(None, 16, 'bold')
        )
        header_label.pack(anchor='w')

        # Main content
        content_frame = ttk.Frame(self, padding=(24, 24, 24, 24))
        content_frame.pack(fill='both', expand=True)
        content_frame.grid_rowconfigure(1, weight=1)
        content_frame.grid_columnconfigure(0, weight=1)

        # URL input section
        input_card = ttk.Frame(content_frame, padding=(16, 16, 16, 16))
        input_card.pack(fill='x', pady=(0, 16))
        url_label = ttk.Label(
            input_card,
            text="Enter News Article URL",
            font=(None, 12)
        )
        url_label.pack(anchor='w', pady=(0, 8))
        input_row = ttk.Frame(input_card)
        input_row.pack(fill='x')
        self.url_entry = ttk.Entry(input_row)
        self.url_entry.pack(side='left', fill='x', expand=True, padx=(0, 8))
        self.scrape_button = ttk.Button(
            input_row,
            text="Summarize",
            command=self._on_scrape
        )
        self.scrape_button.pack(side='right')

        # Progress indicator
        self.progress_frame = ttk.Frame(input_card)
        self.progress_frame.pack(fill='x', pady=(8, 0))
        self.progress_bar = ttk.Progressbar(
            self.progress_frame,
            mode='indeterminate',
            length=100
        )
        self.status_label = ttk.Label(
            self.progress_frame,
            text="",
            font=(None, 9)
        )

        # Results section
        results_frame = ttk.Frame(content_frame)
        results_frame.pack(fill='both', expand=True)
        results_frame.grid_rowconfigure(1, weight=1)
        results_frame.grid_columnconfigure(0, weight=1)

        # Title card
        self.title_card = ttk.Frame(results_frame, padding=(16, 16, 16, 16))
        self.title_card.pack(fill='x', pady=(0, 16))
        self.article_title = ttk.Label(
            self.title_card,
            text="",
            font=(None, 14, 'bold'),
            wraplength=800,
            justify='left'
        )
        self.article_title.pack(anchor='w', fill='x', expand=True)

        # Summary card
        self.summary_card = ttk.Frame(results_frame, padding=(16, 16, 16, 16))
        self.summary_card.pack(fill='both', expand=True)
        self.summary_card.grid_rowconfigure(2, weight=1)  # summary_text expands
        self.summary_card.grid_columnconfigure(0, weight=1)
        summary_header = ttk.Label(
            self.summary_card,
            text="Summary",
            font=(None, 12, 'bold')
        )
        summary_header.grid(row=0, column=0, sticky='w', pady=(0, 8))
        # Keywords section (row 1)
        self.keywords_frame = ttk.Frame(self.summary_card)
        self.keywords_frame.grid(row=1, column=0, sticky='ew', pady=(0, 8))
        self.keywords_frame.grid_columnconfigure(1, weight=1)
        self.keywords_label = ttk.Label(
            self.keywords_frame,
            text="Keywords:",
            font=(None, 10, 'bold')
        )
        self.keywords_label.grid(row=0, column=0, sticky='w', padx=(0, 8))
        self.keywords_text = ttk.Label(
            self.keywords_frame,
            text="",
            font=(None, 10),
            wraplength=800,
            justify='left'
        )
        self.keywords_text.grid(row=0, column=1, sticky='ew')
        # Summary text (row 2)
        self.summary_text = scrolledtext.ScrolledText(
            self.summary_card,
            font=(None, 10),
            background=COLORS['card'],
            foreground=COLORS['text_primary'],
            wrap=tk.WORD,
            borderwidth=0,
            highlightthickness=0
        )
        self.summary_text.grid(row=2, column=0, sticky='nsew', pady=(0, 8))
        # Footer with buttons (row 3)
        self.button_frame = ttk.Frame(self.summary_card)
        self.button_frame.grid(row=3, column=0, sticky='ew', pady=8)
        self.button_frame.grid_columnconfigure(0, weight=1)
        self.view_full_button = ttk.Button(
            self.button_frame,
            text="View Full Article",
            command=self._show_full_article
        )
        self.view_full_button.grid(row=0, column=0, sticky='e', padx=(0, 8))
        self.copy_summary_button = ttk.Button(
            self.button_frame,
            text="Copy Summary",
            command=self._copy_summary
        )
        self.copy_summary_button.grid(row=0, column=1, sticky='e', padx=(0, 8))
        self.open_browser_button = ttk.Button(
            self.button_frame,
            text="Open in Browser",
            command=self._open_in_browser
        )
        self.open_browser_button.grid(row=0, column=2, sticky='e')

        # Initially hide results
        self.title_card.pack_forget()
        self.summary_card.pack_forget()

        # Store the article data
        self.article_data = None
        self.current_url = ""
    
    def _on_scrape(self):
        """Handle the scrape button click"""
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Input Required", "Please enter a URL to scrape.")
            return
        
        # Show progress
        self.progress_bar.pack(fill='x', pady=(8, 4))
        self.status_label.config(text="Scraping article...")
        self.status_label.pack(fill='x')
        self.progress_bar.start(10)
        self.scrape_button.config(state='disabled')
        
        # Hide previous results
        self.title_card.pack_forget()
        self.summary_card.pack_forget()
        
        # Start scraping in a separate thread
        self.current_url = url
        threading.Thread(target=self._scrape_thread, args=(url,), daemon=True).start()
    
    def _scrape_thread(self, url):
        """Run the scraping process in a background thread"""
        try:
            self.article_data = process_article(url, self.api_key)
            # Update UI in the main thread
            self.after(0, self._update_results)
        except Exception as e:
            error_message = str(e)
            self.after(0, lambda: self._show_error(error_message))
    
    def _update_results(self):
        """Update the UI with the scraped results"""
        # Hide progress
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.status_label.pack_forget()
        self.scrape_button.config(state='normal')
        
        if not self.article_data:
            self._show_error("Failed to extract article data.")
            return
        
        # Update title
        self.article_title.config(text=self.article_data['title'])
        self.title_card.pack(fill='x', pady=(0, 16))
        
        # Update summary
        self.summary_text.config(state='normal')
        self.summary_text.delete(1.0, tk.END)
        self.summary_text.insert(tk.END, self.article_data['summary'])
        self.summary_text.config(state='disabled')
        
        # Update keywords
        if self.article_data['keywords']:
            self.keywords_label.grid()
            self.keywords_text.config(text=", ".join(self.article_data['keywords']))
            self.keywords_text.grid()
        else:
            self.keywords_label.grid_remove()
            self.keywords_text.grid_remove()
        
        # Always show keywords_frame (empty if no keywords)
        self.keywords_frame.grid()
        
        # Show summary card
        self.summary_card.pack(fill='both', expand=True)
    
    def _show_error(self, message):
        """Display an error message"""
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.status_label.config(text=f"Error: {message}")
        self.scrape_button.config(state='normal')
    
    def _show_full_article(self):
        """Show the full article text in a new window"""
        if not self.article_data:
            return
        full_window = tk.Toplevel(self)
        full_window.title(f"Full Article: {self.article_data['title']}")
        full_window.geometry("800x600")
        # Header
        header = ttk.Frame(full_window, padding=(16, 16, 16, 16))
        header.pack(fill='x')
        title = ttk.Label(
            header,
            text=self.article_data['title'],
            font=(None, 14, 'bold'),
            wraplength=760,
            justify='left'
        )
        title.pack(anchor='w')
        # Content
        content_frame = ttk.Frame(full_window, padding=(24, 24, 24, 24))
        content_frame.pack(fill='both', expand=True)
        content_card = ttk.Frame(content_frame, padding=(16, 16, 16, 16))
        content_card.pack(fill='both', expand=True)
        text_area = scrolledtext.ScrolledText(
            content_card,
            font=(None, 10),
            background=COLORS['card'],
            foreground='black',
            wrap=tk.WORD,
            borderwidth=0,
            highlightthickness=0
        )
        text_area.pack(fill='both', expand=True)
        text_area.insert(tk.END, self.article_data['text'])
        text_area.config(state='disabled')
    
    def _open_in_browser(self):
        """Open the current article URL in the default web browser"""
        if self.current_url:
            webbrowser.open(self.current_url)
    
    def _copy_summary(self):
        """Copy the summary text to the clipboard"""
        summary = self.summary_text.get(1.0, tk.END).strip()
        self.clipboard_clear()
        self.clipboard_append(summary)
        self.update()  # Keeps clipboard after window closes
        messagebox.showinfo("Copied!", "Summary copied to clipboard.")
    
    def _on_resize(self, event):
        """Dynamically adjust wraplengths for labels on resize"""
        # Set wraplengths to 90% of the current window width, minus padding
        wrap = int(self.winfo_width() * 0.9) - 60
        if wrap < 200:
            wrap = 200
        self.article_title.config(wraplength=wrap)
        self.keywords_text.config(wraplength=wrap)

if __name__ == "__main__":
    app = NewsScraperApp()
    app.mainloop() 