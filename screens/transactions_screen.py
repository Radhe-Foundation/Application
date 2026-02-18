"""
Vernika HRA - Transactions/Payments Screen
Financial transactions recording with attachments
"""

import flet as ft
import os
from datetime import datetime, date
from database.connection import get_db_session
from database.models import Transaction, TransactionAttachment


# Theme colors
PRIMARY = "#2E86AB"
SUCCESS = "#4CAF50"
ERROR = "#F44336"
WARNING = "#FF9800"
INFO = "#17A2B8"
BACKGROUND = "#F8F9FA"
SURFACE = "#FFFFFF"
TEXT_PRIMARY = "#1A1C1E"
TEXT_SECONDARY = "#6C757D"
PURPLE = "#9C27B0"
GREEN = "#4CAF50"
RED = "#F44336"


MAX_FILE_SIZE = 512000  # 500KB in bytes


class TransactionsScreen(ft.Container):
    """Transactions/Payments Recording Screen"""

    def __init__(self, page, user):
        super().__init__()
        self._page = page
        self.user = user
        self.expand = True
        self.bgcolor = BACKGROUND
        self.content = self._build_content()

    def _build_content(self):
        header = ft.Container(
            padding=15,
            bgcolor=PRIMARY,
            content=ft.Row([
                ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    icon_color="WHITE",
                    on_click=self.on_back
                ),
                ft.Icon(ft.Icons.PAYMENT, color="WHITE", size=28),
                ft.Text("Payment & Transactions", size=20,
                        color="WHITE", weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                ft.ElevatedButton(
                    "New Transaction",
                    icon=ft.Icons.ADD,
                    on_click=self._show_add_transaction_dialog,
                    style=ft.ButtonStyle(bgcolor="#FF9800", color="WHITE"),
                ),
            ])
        )

        # Summary cards
        summary = self._build_summary()

        # Transaction list
        transactions_view = self._build_transactions_list()

        return ft.Column([
            header,
            summary,
            ft.Container(
                padding=20,
                content=transactions_view,
                expand=True
            )
        ], expand=True)

    def on_back(self, e):
        from core.navigation import navigate_to_home
        navigate_to_home(self._page, self.user)

    def _get_summary(self):
        """Get transaction summary"""
        db = get_db_session()
        try:
            from sqlalchemy import func

            # Total income
            total_income = db.query(func.sum(Transaction.amount)).filter(
                Transaction.transaction_type == "income",
                Transaction.status == "completed"
            ).scalar() or 0

            # Total expense
            total_expense = db.query(func.sum(Transaction.amount)).filter(
                Transaction.transaction_type == "expense",
                Transaction.status == "completed"
            ).scalar() or 0

            # Pending
            pending = db.query(func.sum(Transaction.amount)).filter(
                Transaction.status == "pending"
            ).scalar() or 0

            # Count
            total_count = db.query(Transaction).count()

            return {
                'total_income': float(total_income),
                'total_expense': float(total_expense),
                'balance': float(total_income) - float(total_expense),
                'pending': float(pending),
                'total_count': total_count
            }
        except Exception as e:
            print(f"Error getting summary: {e}")
            return {'total_income': 0, 'total_expense': 0, 'balance': 0, 'pending': 0, 'total_count': 0}
        finally:
            db.close()

    def _build_summary(self):
        """Build summary cards"""
        summary = self._get_summary()

        return ft.Container(
            padding=15,
            content=ft.Row([
                self._create_summary_card(
                    "Total Income",
                    f"₹{summary['total_income']:,.2f}",
                    ft.Icons.TRENDING_UP,
                    GREEN
                ),
                self._create_summary_card(
                    "Total Expenses",
                    f"₹{summary['total_expense']:,.2f}",
                    ft.Icons.TRENDING_DOWN,
                    RED
                ),
                self._create_summary_card(
                    "Net Balance",
                    f"₹{summary['balance']:,.2f}",
                    ft.Icons.ACCOUNT_BALANCE,
                    PRIMARY
                ),
                self._create_summary_card(
                    "Pending",
                    f"₹{summary['pending']:,.2f}",
                    ft.Icons.PENDING,
                    WARNING
                ),
            ], spacing=20),
            bgcolor=SURFACE
        )

    def _create_summary_card(self, title, value, icon, color):
        """Create a summary card"""
        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Icon(icon, size=28, color=color),
                    ft.Text(value, size=20, weight=ft.FontWeight.BOLD),
                    ft.Text(title, size=12, color=TEXT_SECONDARY),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
                padding=15,
                width=160,
                alignment=ft.alignment.Alignment(0, 0)
            ),
            elevation=2
        )

    def _get_all_transactions(self):
        """Get all transactions"""
        db = get_db_session()
        try:
            transactions = db.query(Transaction).order_by(
                Transaction.transaction_date.desc()
            ).limit(100).all()
            return transactions
        except Exception as e:
            print(f"Error loading transactions: {e}")
            return []
        finally:
            db.close()

    def _build_transactions_list(self):
        """Build transactions list"""
        transactions = self._get_all_transactions()

        if not transactions:
            return ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.RECEIPT_LONG_OUTLINED,
                            size=64, color="#BDBDBD"),
                    ft.Text("No transactions recorded yet.",
                            size=14, color="#757575"),
                    ft.Container(height=10),
                    ft.ElevatedButton(
                        "Record First Transaction",
                        icon=ft.Icons.ADD,
                        on_click=self._show_add_transaction_dialog,
                        style=ft.ButtonStyle(bgcolor=PRIMARY, color="WHITE")
                    ),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.alignment.Alignment(0, 0),
                expand=True
            )

        # Build table rows
        rows = []
        for trans in transactions:
            type_color = GREEN if trans.transaction_type == "income" else RED
            type_icon = ft.Icons.ARROW_UPWARD if trans.transaction_type == "income" else ft.Icons.ARROW_DOWNWARD

            status_colors = {
                "completed": GREEN,
                "pending": WARNING,
                "cancelled": ERROR,
                "failed": ERROR
            }
            status_color = status_colors.get(trans.status, TEXT_SECONDARY)

            # Get attachments count
            db = get_db_session()
            try:
                attachments_count = db.query(TransactionAttachment).filter(
                    TransactionAttachment.transaction_id == trans.id
                ).count()
            except:
                attachments_count = 0
            finally:
                db.close()

            rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(
                            ft.Container(
                                content=ft.Row([
                                    ft.Icon(type_icon, size=16,
                                            color=type_color),
                                    ft.Text(trans.transaction_type.title(),
                                            size=12, color=type_color),
                                ], spacing=5),
                                width=80,
                            )
                        ),
                        ft.DataCell(
                            ft.Text(f"₹{trans.amount:,.2f}", size=13, weight=ft.FontWeight.BOLD)),
                        ft.DataCell(ft.Text(trans.category or "-", size=12)),
                        ft.DataCell(
                            ft.Text(trans.description or "-", size=11)),
                        ft.DataCell(
                            ft.Text(str(trans.transaction_date), size=11)),
                        ft.DataCell(
                            ft.Text(trans.payment_method.title(), size=11)),
                        ft.DataCell(ft.Container(
                            content=ft.Text(trans.status.title(),
                                            size=10, color="WHITE"),
                            bgcolor=status_color,
                            padding=ft.padding.symmetric(
                                horizontal=6, vertical=2),
                            border_radius=4,
                        )),
                        ft.DataCell(
                            ft.Row([
                                ft.IconButton(
                                    icon=ft.Icons.ATTACHMENT,
                                    icon_color=PRIMARY if attachments_count > 0 else TEXT_SECONDARY,
                                    tooltip=f"{attachments_count} attachments",
                                    scale=0.7,
                                    on_click=lambda e, tid=trans.id: self._show_attachments(
                                        tid)
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.EDIT,
                                    icon_color=PRIMARY,
                                    on_click=lambda e, tid=trans.id: self._show_edit_transaction(
                                        tid),
                                    scale=0.7
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.DELETE,
                                    icon_color=ERROR,
                                    on_click=lambda e, tid=trans.id: self._delete_transaction(
                                        tid),
                                    scale=0.7
                                ),
                            ], spacing=0)
                        ),
                    ]
                )
            )

        return ft.Column([
            ft.Row([
                ft.Text("Transaction History", size=18,
                        weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                ft.ElevatedButton(
                    "Export Excel",
                    icon=ft.Icons.DOWNLOAD,
                    on_click=self._export_to_excel,
                    style=ft.ButtonStyle(bgcolor=SUCCESS, color="WHITE"),
                ),
            ]),
            ft.Container(height=15),
            ft.DataTable(
                columns=[
                    ft.DataColumn(label=ft.Text("Type")),
                    ft.DataColumn(label=ft.Text("Amount")),
                    ft.DataColumn(label=ft.Text("Category")),
                    ft.DataColumn(label=ft.Text("Description")),
                    ft.DataColumn(label=ft.Text("Date")),
                    ft.DataColumn(label=ft.Text("Method")),
                    ft.DataColumn(label=ft.Text("Status")),
                    ft.DataColumn(label=ft.Text("Actions")),
                ],
                rows=rows,
                expand=True,
            ),
        ], scroll=ft.ScrollMode.AUTO)

    def _show_add_transaction_dialog(self, e=None):
        """Show add transaction dialog"""
        # Transaction type
        type_group = ft.RadioGroup(
            content=ft.Row([
                ft.Radio(value="income", label="Income"),
                ft.Radio(value="expense", label="Expense"),
            ], spacing=20),
            value="expense"
        )

        # Category options
        income_categories = [
            "Client Payment", "Salary Advance", "Investment", "Refund", "Other Income"
        ]
        expense_categories = [
            "Salary", "Vendor Payment", "Office Supplies", "Utilities",
            "Marketing", "Travel", "Maintenance", "Software", "Other Expense"
        ]

        category_options = [ft.dropdown.Option(
            cat, cat) for cat in expense_categories]
        category_dropdown = ft.Dropdown(
            label="Category *",
            options=category_options,
            width=250
        )

        # Update categories based on type
        def update_categories(e):
            if type_group.value == "income":
                category_dropdown.options = [ft.dropdown.Option(
                    cat, cat) for cat in income_categories]
            else:
                category_dropdown.options = [ft.dropdown.Option(
                    cat, cat) for cat in expense_categories]
            self._page.update()

        type_group.on_change = update_categories

        amount_field = ft.TextField(
            label="Amount *", width=200)
        description_field = ft.TextField(
            label="Description", width=400, multiline=True)
        date_field = ft.TextField(
            label="Date (YYYY-MM-DD)", width=200, value=datetime.now().strftime('%Y-%m-%d'))
        ref_field = ft.TextField(label="Reference Number", width=200)

        # Payment method
        method_options = [
            ft.dropdown.Option("cash", "Cash"),
            ft.dropdown.Option("bank_transfer", "Bank Transfer"),
            ft.dropdown.Option("upi", "UPI"),
            ft.dropdown.Option("credit_card", "Credit Card"),
            ft.dropdown.Option("debit_card", "Debit Card"),
            ft.dropdown.Option("cheque", "Cheque"),
            ft.dropdown.Option("other", "Other"),
        ]
        method_dropdown = ft.Dropdown(
            label="Payment Method",
            options=method_options,
            width=200,
            value="cash"
        )

        # Status
        status_options = [
            ft.dropdown.Option("completed", "Completed"),
            ft.dropdown.Option("pending", "Pending"),
            ft.dropdown.Option("cancelled", "Cancelled"),
        ]
        status_dropdown = ft.Dropdown(
            label="Status",
            options=status_options,
            width=150,
            value="completed"
        )

        # Attachment info
        attachment_info = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.INFO_OUTLINE, size=16, color=INFO),
                ft.Text("You can add attachments (max 500KB each) after creating the transaction",
                        size=11, color=TEXT_SECONDARY),
            ]),
            bgcolor="#E3F2FD",
            padding=10,
            border_radius=8
        )

        def save(e):
            if not amount_field.value or not amount_field.value.replace('.', '').isdigit():
                self._show_error("Valid amount required!")
                return

            if not category_dropdown.value:
                self._show_error("Category required!")
                return

            try:
                trans_date = datetime.strptime(
                    date_field.value, '%Y-%m-%d').date()
            except:
                trans_date = date.today()

            db = get_db_session()
            try:
                new_trans = Transaction(
                    transaction_type=type_group.value,
                    amount=float(amount_field.value),
                    category=category_dropdown.value,
                    description=description_field.value or None,
                    transaction_date=trans_date,
                    payment_method=method_dropdown.value or "cash",
                    reference_number=ref_field.value or None,
                    status=status_dropdown.value or "completed",
                    created_by_id=self._get_user_id()
                )
                db.add(new_trans)
                db.commit()

                self._show_success("Transaction recorded!")
                self._close_dialog()
                self._refresh()
            except Exception as ex:
                self._show_error(f"Error: {str(ex)}")
            finally:
                db.close()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("New Transaction"),
            content=ft.Container(
                content=ft.Column([
                    type_group,
                    amount_field,
                    category_dropdown,
                    description_field,
                    ft.Row([date_field, ref_field], spacing=10),
                    ft.Row([method_dropdown, status_dropdown], spacing=10),
                    attachment_info,
                ], spacing=10, scroll=ft.ScrollMode.AUTO),
                width=450,
            ),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda e: self._close_dialog()),
                ft.ElevatedButton("Save", on_click=save, style=ft.ButtonStyle(
                    bgcolor=SUCCESS, color="WHITE")),
            ]
        )

        self._page.overlay.append(dialog)
        dialog.open = True
        self._page.update()

    def _show_edit_transaction(self, trans_id):
        """Show edit transaction dialog"""
        db = get_db_session()
        try:
            trans = db.query(Transaction).filter(
                Transaction.id == trans_id).first()
            if not trans:
                self._show_error("Transaction not found")
                return
        except:
            self._show_error("Error loading transaction")
            return
        finally:
            db.close()

        # Pre-fill values
        amount_field = ft.TextField(
            label="Amount *", width=200, value=str(trans.amount))
        description_field = ft.TextField(
            label="Description", width=400, multiline=True, value=trans.description or "")
        date_field = ft.TextField(
            label="Date", width=200, value=str(trans.transaction_date))
        ref_field = ft.TextField(
            label="Reference Number", width=200, value=trans.reference_number or "")

        # Category options
        income_categories = ["Client Payment", "Salary Advance",
                             "Investment", "Refund", "Other Income"]
        expense_categories = ["Salary", "Vendor Payment", "Office Supplies",
                              "Utilities", "Marketing", "Travel", "Maintenance", "Software", "Other Expense"]

        if trans.transaction_type == "income":
            cat_options = [ft.dropdown.Option(
                cat, cat) for cat in income_categories]
        else:
            cat_options = [ft.dropdown.Option(
                cat, cat) for cat in expense_categories]

        category_dropdown = ft.Dropdown(
            label="Category *",
            options=cat_options,
            width=250,
            value=trans.category
        )

        # Payment method
        method_options = [
            ft.dropdown.Option("cash", "Cash"),
            ft.dropdown.Option("bank_transfer", "Bank Transfer"),
            ft.dropdown.Option("upi", "UPI"),
            ft.dropdown.Option("credit_card", "Credit Card"),
            ft.dropdown.Option("debit_card", "Debit Card"),
            ft.dropdown.Option("cheque", "Cheque"),
        ]
        method_dropdown = ft.Dropdown(
            label="Payment Method",
            options=method_options,
            width=200,
            value=trans.payment_method
        )

        # Status
        status_options = [
            ft.dropdown.Option("completed", "Completed"),
            ft.dropdown.Option("pending", "Pending"),
            ft.dropdown.Option("cancelled", "Cancelled"),
        ]
        status_dropdown = ft.Dropdown(
            label="Status",
            options=status_options,
            width=150,
            value=trans.status
        )

        def save(e):
            try:
                trans_date = datetime.strptime(
                    date_field.value, '%Y-%m-%d').date()
            except:
                trans_date = trans.transaction_date

            db = get_db_session()
            try:
                db.query(Transaction).filter(Transaction.id == trans_id).update({
                    Transaction.amount: float(amount_field.value) if amount_field.value.replace('.', '').isdigit() else trans.amount,
                    Transaction.category: category_dropdown.value,
                    Transaction.description: description_field.value or None,
                    Transaction.transaction_date: trans_date,
                    Transaction.payment_method: method_dropdown.value,
                    Transaction.reference_number: ref_field.value or None,
                    Transaction.status: status_dropdown.value,
                })
                db.commit()

                self._show_success("Transaction updated!")
                self._close_dialog()
                self._refresh()
            except Exception as ex:
                self._show_error(f"Error: {str(ex)}")
            finally:
                db.close()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Edit Transaction"),
            content=ft.Container(
                content=ft.Column([
                    amount_field,
                    category_dropdown,
                    description_field,
                    ft.Row([date_field, ref_field], spacing=10),
                    ft.Row([method_dropdown, status_dropdown], spacing=10),
                ], spacing=10),
                width=450,
            ),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda e: self._close_dialog()),
                ft.ElevatedButton("Update", on_click=save, style=ft.ButtonStyle(
                    bgcolor=PRIMARY, color="WHITE")),
            ]
        )

        self._page.overlay.append(dialog)
        dialog.open = True
        self._page.update()

    def _show_attachments(self, trans_id):
        """Show attachments for a transaction"""
        db = get_db_session()
        try:
            trans = db.query(Transaction).filter(
                Transaction.id == trans_id).first()
            if not trans:
                self._show_error("Transaction not found")
                return

            attachments = db.query(TransactionAttachment).filter(
                TransactionAttachment.transaction_id == trans_id
            ).all()
        except:
            attachments = []
        finally:
            db.close()

        # Build attachment list
        attach_list = ft.Column()
        if attachments:
            for att in attachments:
                size_kb = att.file_size / 1024
                attach_list.controls.append(
                    ft.Container(
                        padding=10,
                        bgcolor="#F5F5F5",
                        border_radius=8,
                        margin=ft.margin.only(bottom=5),
                        content=ft.Row([
                            ft.Icon(ft.Icons.ATTACHMENT, color=PRIMARY),
                            ft.Text(att.file_name, expand=True),
                            ft.Text(f"{size_kb:.1f} KB", size=11,
                                    color=TEXT_SECONDARY),
                        ])
                    )
                )
        else:
            attach_list.controls.append(
                ft.Text("No attachments yet", size=12, color=TEXT_SECONDARY)
            )

        # Add attachment button
        def add_attachment(e):
            self._show_add_attachment_dialog(trans_id)

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Attachments - ₹{trans.amount:,.2f}"),
            content=ft.Container(
                content=ft.Column([
                    ft.Text(f"Category: {trans.category}",
                            size=12, color=TEXT_SECONDARY),
                    ft.Text(f"Date: {trans.transaction_date}",
                            size=12, color=TEXT_SECONDARY),
                    ft.Divider(),
                    ft.Text("Attachments:", size=13,
                            weight=ft.FontWeight.BOLD),
                    attach_list,
                    ft.Container(height=10),
                    ft.ElevatedButton(
                        "Add Attachment (Max 500KB)",
                        icon=ft.Icons.ADD,
                        on_click=add_attachment,
                        style=ft.ButtonStyle(bgcolor=SUCCESS, color="WHITE")
                    ),
                ], scroll=ft.ScrollMode.AUTO),
                width=400,
                height=400,
            ),
            actions=[
                ft.TextButton(
                    "Close", on_click=lambda e: self._close_dialog()),
            ]
        )

        self._page.overlay.append(dialog)
        dialog.open = True
        self._page.update()

    def _show_add_attachment_dialog(self, trans_id):
        """Show add attachment dialog"""
        # Note: File picker would require additional setup
        # For now, we'll just show a placeholder
        self._show_info("File upload feature - Enter file path")

        file_path = ft.TextField(
            label="File Path", width=350, hint_text="Enter full path to file")

        def save_attachment(e):
            if not file_path.value:
                self._show_error("File path required")
                return

            if not os.path.exists(file_path.value):
                self._show_error("File not found")
                return

            file_size = os.path.getsize(file_path.value)
            if file_size > MAX_FILE_SIZE:
                self._show_error(
                    f"File too large! Max 500KB allowed (yours: {file_size/1024:.1f}KB)")
                return

            # Copy file to assets
            file_name = os.path.basename(file_path.value)

            db = get_db_session()
            try:
                att = TransactionAttachment(
                    transaction_id=trans_id,
                    file_path=file_path.value,
                    file_name=file_name,
                    file_size=file_size,
                    uploaded_by_id=self._get_user_id()
                )
                db.add(att)
                db.commit()

                self._show_success("Attachment added!")
                self._close_dialog()
            except Exception as ex:
                self._show_error(f"Error: {str(ex)}")
            finally:
                db.close()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Add Attachment"),
            content=ft.Column([
                ft.Text("Max file size: 500KB", size=11, color=TEXT_SECONDARY),
                file_path,
            ], spacing=10),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda e: self._close_dialog()),
                ft.ElevatedButton("Add", on_click=save_attachment, style=ft.ButtonStyle(
                    bgcolor=SUCCESS, color="WHITE")),
            ]
        )

        self._page.overlay.append(dialog)
        dialog.open = True
        self._page.update()

    def _delete_transaction(self, trans_id):
        """Delete a transaction"""
        def confirm(e):
            db = get_db_session()
            try:
                # Delete attachments first
                db.query(TransactionAttachment).filter(
                    TransactionAttachment.transaction_id == trans_id
                ).delete()
                # Delete transaction
                db.query(Transaction).filter(
                    Transaction.id == trans_id).delete()
                db.commit()

                self._show_success("Transaction deleted!")
                self._close_dialog()
                self._refresh()
            except Exception as ex:
                self._show_error(f"Error: {str(ex)}")
            finally:
                db.close()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Delete Transaction?", color=ERROR),
            content=ft.Text(
                "This will also delete all attachments. This cannot be undone."),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda e: self._close_dialog()),
                ft.ElevatedButton("Delete", on_click=confirm, style=ft.ButtonStyle(
                    bgcolor=ERROR, color="WHITE")),
            ]
        )

        self._page.overlay.append(dialog)
        dialog.open = True
        self._page.update()

    def _export_to_excel(self, e=None):
        """Export transactions to Excel"""
        try:
            import pandas as pd

            transactions = self._get_all_transactions()

            data = []
            for trans in transactions:
                data.append({
                    'Type': trans.transaction_type,
                    'Amount': trans.amount,
                    'Category': trans.category,
                    'Description': trans.description,
                    'Date': trans.transaction_date,
                    'Payment Method': trans.payment_method,
                    'Reference': trans.reference_number,
                    'Status': trans.status
                })

            if data:
                df = pd.DataFrame(data)

                output_dir = os.path.expanduser("~/Downloads")
                os.makedirs(output_dir, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = os.path.join(
                    output_dir, f"transactions_{timestamp}.xlsx")

                df.to_excel(output_path, index=False, engine='openpyxl')
                self._show_success(f"Exported to {output_path}")
            else:
                self._show_error("No data to export")

        except Exception as ex:
            self._show_error(f"Export error: {str(ex)}")

    def _get_user_id(self):
        """Get current user ID"""
        if isinstance(self.user, dict):
            return self.user.get('id')
        return None

    def _close_dialog(self):
        for overlay in self._page.overlay:
            if isinstance(overlay, ft.AlertDialog) and overlay.open:
                overlay.open = False
        self._page.update()

    def _refresh(self):
        self.content = self._build_content()
        self._page.update()

    def _show_success(self, msg):
        snack = ft.SnackBar(content=ft.Text(msg), bgcolor=SUCCESS)
        self._page.overlay.append(snack)
        snack.open = True
        self._page.update()

    def _show_error(self, msg):
        snack = ft.SnackBar(content=ft.Text(msg), bgcolor=ERROR)
        self._page.overlay.append(snack)
        snack.open = True
        self._page.update()

    def _show_info(self, msg):
        snack = ft.SnackBar(content=ft.Text(msg), bgcolor=INFO)
        self._page.overlay.append(snack)
        snack.open = True
        self._page.update()


def show_transactions(page, user):
    """Helper function to show transactions screen"""
    page.clean()
    page.add(TransactionsScreen(page, user))
