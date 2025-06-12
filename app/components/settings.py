import flet as ft


class Setting(ft.Container):
    def __init__(self, callback):
        super().__init__()
        self.expand = 1
        self.padding = 10

        self.transcription_settings = {}
        self.callback = callback

        self.content = ft.Column(
            [
                ft.Text(
                    "1.ファイルを選択",
                    theme_style=ft.TextThemeStyle.HEADLINE_MEDIUM,
                ),
                ft.Container(
                    content=ft.Column(
                        [
                            ft.OutlinedButton(
                                "ファイルを選択",
                                icon=ft.Icons.UPLOAD_FILE,
                                on_click=lambda _: pick_files_dialog.pick_files(
                                    allowed_extensions=ALLOWED_EXTENSIONS,
                                ),
                            ),
                            selected_file,
                        ],
                    ),
                    margin=10,
                ),
                ft.Text(
                    "2.設定",
                    theme_style=ft.TextThemeStyle.HEADLINE_MEDIUM,
                ),
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Row(
                                [
                                    model_dropdown,
                                    precision_dropdown,
                                ]
                            ),
                        ]
                    ),
                    margin=10,
                ),
                ft.Text(
                    "3.保存先を選択",
                    theme_style=ft.TextThemeStyle.HEADLINE_MEDIUM,
                ),
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Column(
                                [
                                    ft.OutlinedButton(
                                        "フォルダを選択",
                                        icon=ft.Icons.FOLDER_OPEN,
                                        on_click=lambda _: output_directory_picker.get_directory_path(),
                                    ),
                                    output_directory,
                                ]
                            ),
                        ]
                    ),
                    margin=10,
                ),
                ft.Text(
                    "4.文字起こし開始",
                    theme_style=ft.TextThemeStyle.HEADLINE_MEDIUM,
                ),
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Row(
                                [
                                    start_button,
                                    progress_ring,
                                ]
                            ),
                        ]
                    ),
                    margin=10,
                ),
            ]
        )
