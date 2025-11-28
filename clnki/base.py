from __future__ import annotations
from abc import ABC, abstractmethod
import os
import functools

# TODO: Switch to python 3.10+ for Union types
    
class ExitApp(Exception):
    pass


class Navigate(Exception):
    def __init__(self, next_page: Page | None, **kwargs):
        super().__init__()
        self.next_page = next_page
        self.next_kwargs = kwargs or {}  # so that ** can always be applied.


def clear_terminal() -> None:
    os.system("cls" if os.name == "nt" else "clear")


class Page(ABC):
    """Interface for all pages in Clnki."""

    def __init__(self, app: App):
        self.app = app

    @staticmethod
    def global_parser(func):
        """
        A decorator to wrap over any argparser implementation so that
        the App's global_parser applies first.
        """
        @functools.wraps(func)
        def inner(self, raw_input: str):
            if self.app is not None:
                self.app.global_parser(raw_input)
            return func(self, raw_input)
        return inner
    
    @abstractmethod
    def render(self) -> None:
        """Draw the page content to the terminal."""
        raise NotImplementedError
    
    @abstractmethod
    def next_page(self) -> Page | None:
        """
        Decide the next Page.

        Return:
            - Page: go to that page
            - None: exit the app
        """
        raise NotImplementedError
    
    def on_mount(self) -> None:
        """Run before the Page is rendered."""
        pass

    def on_exit(self) -> None:
        """Run when the page exits."""
        pass

    @global_parser
    def argparser(self, raw_input: str):
        """
        Preprocess all inputs to the Page.
        If the Page has no argparser this does not need to be overriden.

        Returns: argparse.Namespace object
        """
        pass

    


class App:
    """Base application class. Clnki will have additional attributes like 'collection'."""

    def __init__(self):
        self.page = None
        self.pages = {}
    
    def run(self) -> None:
        """
        In addition to initialization, this is also run when switching pages if next_page()
        does not return, in conjunction with self.page = {next page}.
        """
        next_kwargs = {}
        while self.page is not None:
            try:
                self.page.on_mount(**next_kwargs)
                clear_terminal()
                self.page.render()

                try:
                    next_page, next_kwargs = self.page.next_page()  # next_kwargs is {} if there is no argument.
                except Navigate as nav:
                    next_page, next_kwargs = nav.next_page, nav.next_kwargs

                self.page.on_exit()
                self.page = next_page

            except ExitApp:
                # can do something later here
                self.on_quit()
                quit()
        self.on_quit()
        quit()
    
    def on_quit(self):
        pass
    
    def global_parser(raw_input: str):
        pass



