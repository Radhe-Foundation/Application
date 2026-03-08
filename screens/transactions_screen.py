"""
Vernika HRA - Transactions/Payments Screen
Financial transactions recording with attachments
"""

import flet as ft
import os
import base64
import io
from datetime import datetime, date
from database.session_manager import get_session, get_db_session, check_db_connection
from database.models import Transaction, TransactionAttachment, BillingRequest, BillingRequestAttachment

# Import Supabase storage for cloud file uploads
from utils.supabase_storage import upload_to_supabase, get_storage
from config import MAX_UPLOAD_SIZE_MB


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


# File size limit - use config value converted to bytes
MAX_FILE_SIZE = MAX_UPLOAD_SIZE_MB * 1024 * 1024  # Convert MB to bytes


def _safe_navigate_to_home(page, user=None):
    """Safely navigate to home screen"""
    try:
        from core.navigation import navigate_to_home
        navigate_to_home(page, user)
    except ImportError:
        try:
            from screens.admin_screen import AdminScreen
            from screens.employee_screen import EmployeeScreen
            page.clean()
            if user and isinstance(user, dict):
                role = user.get('role', 'employee').lower()
            elif user and hasattr(user, 'role'):
                role = user.role.name.lower() if user.role else 'employee'
            else:
                role = 'employee'
            if role == 'admin':
                page.add(AdminScreen(page, user))
            else:
                page.add(EmployeeScreen(page, user))
        except Exception as e:
            print(f"Navigation error: {e}")
            from screens.login_screen import LoginScreen
            page.clean()
            page.add(LoginScreen(page))


class TransactionsScreen(ft.Container):
    """Transactions/Payments Recording Screen"""

    def __init__(self, page, user):
        super().__init__()
        self._page = page
        self.user = user
        self.expand = True
        self.bgcolor = BACKGROUND
        self._file_picker = None
        self._view_mode = "transactions"  # Default view mode: transactions or billing
        self.content = self._build_content()

    def _init_file_picker(self):
        """Initialize file picker for attachments"""
        if not self._file_picker:
            self._file_picker = ft.FilePicker()
            # Use overlay instead of deprecated services (Flet 0.80+)
            if self._file_picker not in self._page.overlay:
                self._page.overlay.append(self._file_picker)

    def _build_content(self):
        header = ft.Container(
            padding=15,
            bgcolor=PRIMARY,
            content=ft.Row([
                ft.Icon(ft.Icons.PAYMENT, color="WHITE", size=28),
                ft.Text("Payment & Transactions", size=20,
                        color="WHITE", weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                # Tab selector for Transactions vs Billing Requests
                ft.Container(
                    content=ft.SegmentedButton(
                        segments=[
                            ft.Segment(
                                value="transactions",
                                label=ft.Text("Transactions", size=12),
                            ),
                            ft.Segment(
                                value="billing",
                                label=ft.Text("Billing Requests", size=12),
                            ),
                        ],
                        selected=[self._view_mode],
                        on_change=self._on_view_mode_change,
                    ),
                    bgcolor="white12",
                    border_radius=8,
                    padding=3,
                ),
                ft.Container(width=10),
                ft.ElevatedButton(
                    "New Transaction" if self._view_mode == "transactions" else "New Request",
                    icon=ft.Icons.ADD,
                    on_click=self._show_add_transaction_dialog if self._view_mode == "transactions" else self._show_add_billing_request_dialog,
                    style=ft.ButtonStyle(bgcolor="#FF9800", color="WHITE"),
                ),
            ])
        )

        # Build content based on view mode
        if self._view_mode == "billing":
            # Show billing requests view
            content_view = self._build_billing_requests_view()
        else:
            # Show transactions view (original)
            # Summary cards
            summary = self._build_summary()

            # Transaction list
            transactions_view = self._build_transactions_list()

            content_view = ft.Column([
                summary,
                ft.Container(
                    padding=20,
                    content=transactions_view,
                    expand=True
                )
            ], expand=True)

        return ft.Column([
            header,
            content_view
        ], expand=True)

    def on_back(self, e):
        """Handle back navigation"""
        _safe_navigate_to_home(self._page, self.user)

    def _on_view_mode_change(self, e):
        """Handle view mode change between transactions and billing requests"""
        selected = e.control.selected
        if isinstance(selected, list) and selected:
            self._view_mode = selected[0]
        elif isinstance(selected, str):
            self._view_mode = selected

        # Rebuild content based on view mode
        self._refresh()

    def _is_admin(self):
        """Check if current user is admin"""
        if isinstance(self.user, dict):
            role = self.user.get('role', '').lower()
            return role == 'admin'
        return False

    def _get_employee_id(self):
        """Get employee ID from user"""
        user_id = None
        if isinstance(self.user, dict):
            user_id = self.user.get('id')

        if not user_id:
            return None

        db = get_db_session()
        try:
            from database.models import Employee
            emp = db.query(Employee).filter(
                Employee.user_id == user_id).first()
            if emp:
                return emp.id
        except Exception as e:
            print(f"Error getting employee ID: {e}")
        finally:
            db.close()
        return None

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
            except Exception:
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
                ft.Text(f"You can add attachments (max {MAX_UPLOAD_SIZE_MB}MB each) after creating the transaction",
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
            except Exception:
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
        except Exception:
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
            except Exception:
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
        """Show attachments for a transaction with preview option"""
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
        except Exception as e:
            print(f"Error loading attachments: {e}")
            attachments = []
        finally:
            db.close()

        # Build attachment list with preview and download options
        attach_list = ft.Column()
        if attachments:
            for att in attachments:
                size_kb = att.file_size / 1024 if att.file_size else 0

                # Determine file type icon
                file_ext = ""
                if att.file_name:
                    file_ext = att.file_name.split(
                        '.')[-1].lower() if '.' in att.file_name else ""

                file_icon = ft.Icons.ATTACHMENT
                if file_ext in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                    file_icon = ft.Icons.IMAGE
                elif file_ext == 'pdf':
                    file_icon = ft.Icons.PICTURE_AS_PDF
                elif file_ext in ['doc', 'docx']:
                    file_icon = ft.Icons.DESCRIPTION
                elif file_ext in ['xls', 'xlsx']:
                    file_icon = ft.Icons.TABLE_CHART

                attach_list.controls.append(
                    ft.Container(
                        padding=10,
                        bgcolor="#F5F5F5",
                        border_radius=8,
                        margin=ft.margin.only(bottom=5),
                        content=ft.Row([
                            ft.Icon(file_icon, color=PRIMARY, size=20),
                            ft.Column([
                                ft.Text(att.file_name or "Unknown file",
                                        size=12, weight=ft.FontWeight.BOLD),
                                ft.Text(f"{size_kb:.1f} KB",
                                        size=10, color=TEXT_SECONDARY),
                            ], spacing=2, expand=True),
                            # Preview button
                            ft.IconButton(
                                icon=ft.Icons.VISIBILITY,
                                icon_color=INFO,
                                tooltip="Preview",
                                scale=0.7,
                                on_click=lambda e, a=att: self._preview_attachment(
                                    a)
                            ),
                            # Download button
                            ft.IconButton(
                                icon=ft.Icons.DOWNLOAD,
                                icon_color=SUCCESS,
                                tooltip="Download",
                                scale=0.7,
                                on_click=lambda e, a=att: self._download_attachment(
                                    a.file_path, a.file_name)
                            ),
                            # Delete button
                            ft.IconButton(
                                icon=ft.Icons.DELETE,
                                icon_color=ERROR,
                                tooltip="Delete",
                                scale=0.7,
                                on_click=lambda e, a=att: self._delete_attachment(
                                    a, trans_id)
                            ),
                        ], spacing=10)
                    )
                )
        else:
            attach_list.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.FOLDER_OPEN, size=32,
                                color=TEXT_SECONDARY),
                        ft.Text("No attachments yet", size=12,
                                color=TEXT_SECONDARY),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=20,
                )
            )

        # Add attachment button
        def add_attachment(e):
            self._show_add_attachment_dialog(trans_id)

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Attachments - ₹{trans.amount:,.2f}"),
            content=ft.Container(
                content=ft.Column([
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.RECEIPT, color=PRIMARY, size=20),
                            ft.Text(f"Category: {trans.category}",
                                    size=12, color=TEXT_SECONDARY),
                        ], spacing=10),
                        padding=10,
                        bgcolor="#E3F2FD",
                        border_radius=8,
                    ),
                    ft.Text(f"Date: {trans.transaction_date}",
                            size=11, color=TEXT_SECONDARY),
                    ft.Divider(),
                    ft.Text("Attachments:", size=13,
                            weight=ft.FontWeight.BOLD),
                    ft.Container(
                        content=attach_list,
                        height=250,
                    ),
                    ft.Container(height=10),
                    ft.ElevatedButton(
                        f"Add Attachment (Max {MAX_UPLOAD_SIZE_MB}MB)",
                        icon=ft.Icons.ADD,
                        on_click=add_attachment,
                        style=ft.ButtonStyle(bgcolor=SUCCESS, color="WHITE")
                    ),
                ], scroll=ft.ScrollMode.AUTO),
                width=450,
                height=450,
            ),
            actions=[
                ft.TextButton(
                    "Close", on_click=lambda e: self._close_dialog()),
            ]
        )

        self._page.overlay.append(dialog)
        dialog.open = True
        self._page.update()

    def _preview_attachment(self, attachment):
        """Preview an attachment file - supports Supabase URLs, file path, and database binary data"""
        if not attachment:
            self._show_error("Attachment not found")
            return

        # Determine file type
        file_ext = ""
        if attachment.file_name:
            file_ext = attachment.file_name.split(
                '.')[-1].lower() if '.' in attachment.file_name else ""

        # Check if it's an image
        image_extensions = ['jpg', 'jpeg', 'png', 'gif', 'webp']

        if file_ext in image_extensions:
            # Show image preview - try Supabase URL first, then database, then file path
            img_src = None
            try:
                # Check if file_path is a Supabase URL
                if attachment.file_path and attachment.file_path.startswith('http'):
                    # Use Supabase URL directly
                    img_src = attachment.file_path
                # Check if we have binary data in database
                elif hasattr(attachment, 'file_data') and attachment.file_data:
                    # Use base64 encoded data from database
                    import base64
                    img_bytes = attachment.file_data
                    b64_str = base64.b64encode(img_bytes).decode()
                    img_src = f"data:image/{file_ext};base64,{b64_str}"
                elif attachment.file_path and os.path.exists(attachment.file_path):
                    # Fall back to local file path
                    img_src = attachment.file_path

                if not img_src:
                    self._show_error("File not found")
                    return

                dialog = ft.AlertDialog(
                    modal=True,
                    title=ft.Text(f"Preview: {attachment.file_name}"),
                    content=ft.Container(
                        content=ft.Image(
                            src=img_src,
                            width=400,
                            height=400,
                            fit="contain",
                        ),
                        width=420,
                        height=420,
                    ),
                    actions=[
                        ft.TextButton(
                            "Close", on_click=lambda e: self._close_dialog()),
                        ft.ElevatedButton(
                            "Download",
                            icon=ft.Icons.DOWNLOAD,
                            on_click=lambda e: self._download_attachment(
                                attachment.file_path, attachment.file_name, attachment.file_data if hasattr(attachment, 'file_data') else None),
                            style=ft.ButtonStyle(
                                bgcolor=PRIMARY, color="WHITE")
                        ),
                    ]
                )
                self._page.overlay.append(dialog)
                dialog.open = True
                self._page.update()
            except Exception as e:
                self._show_error(f"Error previewing image: {str(e)}")
        else:
            # For non-image files, just show info and offer download
            size_kb = attachment.file_size / 1024 if attachment.file_size else 0
            # Check if it's a cloud file
            is_cloud = attachment.file_path and attachment.file_path.startswith(
                'http')
            source_text = "Cloud Storage" if is_cloud else "Local"

            dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text(f"File Info: {attachment.file_name}"),
                content=ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.INFO_OUTLINE, size=48, color=INFO),
                        ft.Container(height=10),
                        ft.Text(attachment.file_name, size=14,
                                weight=ft.FontWeight.BOLD),
                        ft.Text(f"Size: {size_kb:.1f} KB",
                                size=12, color=TEXT_SECONDARY),
                        ft.Text(f"Type: {file_ext.upper()}",
                                size=12, color=TEXT_SECONDARY),
                        ft.Text(f"Source: {source_text}",
                                size=11, color=SUCCESS if is_cloud else TEXT_SECONDARY),
                        ft.Container(height=10),
                        ft.Text("Preview not available for this file type.",
                                size=11, color=TEXT_SECONDARY),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=20,
                ),
                actions=[
                    ft.TextButton(
                        "Close", on_click=lambda e: self._close_dialog()),
                    ft.ElevatedButton(
                        "Download",
                        icon=ft.Icons.DOWNLOAD,
                        on_click=lambda e: self._download_attachment(
                            attachment.file_path, attachment.file_name, attachment.file_data if hasattr(attachment, 'file_data') else None),
                        style=ft.ButtonStyle(bgcolor=PRIMARY, color="WHITE")
                    ),
                ]
            )
            self._page.overlay.append(dialog)
            dialog.open = True
            self._page.update()

    def _delete_attachment(self, attachment, trans_id):
        """Delete an attachment"""
        def confirm(e):
            db = get_db_session()
            try:
                att = db.query(TransactionAttachment).filter(
                    TransactionAttachment.id == attachment.id
                ).first()
                if att:
                    db.delete(att)
                    db.commit()
                    self._show_success("Attachment deleted!")
                    self._close_dialog()
                    # Refresh to show updated list
                    self._show_attachments(trans_id)
            except Exception as ex:
                self._show_error(f"Error deleting: {str(ex)}")
            finally:
                db.close()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Delete Attachment?", color=ERROR),
            content=ft.Text(
                f"Delete '{attachment.file_name}'? This cannot be undone."),
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

    def _show_add_attachment_dialog(self, trans_id):
        """Show add attachment dialog with file picker - uploads to Supabase Cloud Storage"""
        self._init_file_picker()

        file_path = [None]

        def pick_file(e):
            """Pick file using file picker"""
            async def pick_and_save():
                try:
                    files = await self._file_picker.pick_files(
                        dialog_title="Choose attachment file",
                        file_type=ft.FilePickerFileType.ANY,
                    )
                    if files and files[0]:
                        path = files[0].path
                        file_path[0] = path
                        path_input.value = path
                        self._page.update()
                except Exception as ex:
                    print(f"Error picking file: {ex}")

            self._page.run_task(pick_and_save)

        path_input = ft.TextField(
            label="File Path", width=350, hint_text="Enter full path to file or browse")

        browse_btn = ft.ElevatedButton(
            "Browse",
            icon=ft.Icons.FOLDER_OPEN,
            on_click=pick_file,
            style=ft.ButtonStyle(bgcolor=PRIMARY, color="WHITE")
        )

        # Status indicator
        upload_status = ft.Text("", size=11, color=TEXT_SECONDARY)

        def save_attachment(e):
            if not path_input.value:
                self._show_error("File path required")
                return

            if not os.path.exists(path_input.value):
                self._show_error("File not found")
                return

            file_size = os.path.getsize(path_input.value)
            if file_size > MAX_FILE_SIZE:
                self._show_error(
                    f"File too large! Max {MAX_UPLOAD_SIZE_MB}MB allowed (yours: {file_size/1024/1024:.1f}MB)")
                return

            file_name = os.path.basename(path_input.value)

            # Show uploading status
            upload_status.value = "Uploading to cloud..."
            upload_status.color = INFO
            self._page.update()

            # Try to upload to Supabase Cloud Storage
            file_url = None
            upload_success = False
            upload_error = None
            local_file_data = None

            try:
                storage = get_storage()
                if storage.available:
                    # Upload to Supabase Storage
                    success, url_or_error, bucket_path = upload_to_supabase(
                        path_input.value,
                        folder="transaction_attachments",
                        custom_filename=f"trans_{trans_id}_{int(datetime.now().timestamp())}_{file_name}"
                    )

                    if success and url_or_error:
                        file_url = url_or_error
                        upload_success = True
                        print(
                            f"[Transactions] File uploaded to Supabase: {file_url}")
                    else:
                        upload_error = url_or_error
                        print(
                            f"[Transactions] Supabase upload failed: {url_or_error}")
                else:
                    upload_error = "Cloud storage not configured"
                    print("[Transactions] Supabase storage not available")
            except Exception as upload_err:
                upload_error = str(upload_err)
                print(f"[Transactions] Upload error: {upload_err}")

            # If Supabase upload failed or not available, fall back to local storage
            if not upload_success:
                if upload_error:
                    upload_status.value = f"Cloud upload failed: {upload_error}. Saving locally."
                    upload_status.color = WARNING
                    self._page.update()

                try:
                    with open(path_input.value, 'rb') as f:
                        local_file_data = f.read()
                    file_url = path_input.value  # Store local path as fallback
                except Exception as e:
                    self._show_error(f"Error reading file: {str(e)}")
                    return
            else:
                upload_status.value = "Uploaded to cloud!"
                upload_status.color = SUCCESS

            db = get_db_session()
            try:
                att = TransactionAttachment(
                    transaction_id=trans_id,
                    file_path=file_url,  # Store Supabase URL or local path
                    file_name=file_name,
                    file_size=file_size,
                    file_data=local_file_data,  # Keep local backup if available
                    uploaded_by_id=self._get_user_id()
                )
                db.add(att)
                db.commit()

                self._show_success(
                    "Attachment added to cloud!" if upload_success else "Attachment added!")
                self._close_dialog()
            except Exception as ex:
                self._show_error(f"Error: {str(ex)}")
            finally:
                db.close()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Add Attachment"),
            content=ft.Column([
                ft.Text(
                    f"Max file size: {MAX_UPLOAD_SIZE_MB}MB", size=11, color=TEXT_SECONDARY),
                ft.Text(
                    "Files are uploaded to cloud storage for easy access", size=10, color=SUCCESS),
                ft.Row([path_input, browse_btn], spacing=10),
                upload_status,
            ], spacing=10),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda e: self._close_dialog()),
                ft.ElevatedButton("Upload", on_click=save_attachment, style=ft.ButtonStyle(
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
        # Try dict first
        if isinstance(self.user, dict):
            uid = self.user.get('id')
            if uid:
                return uid

        # Try object attribute
        if hasattr(self.user, 'id'):
            return getattr(self.user, 'id')

        # Try from page session
        try:
            if hasattr(self._page, 'session'):
                session_data = self._page.session
                if session_data and isinstance(session_data, dict):
                    user_data = session_data.get('user')
                    if user_data and isinstance(user_data, dict):
                        return user_data.get('id')
        except Exception:
            pass

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

    # ==================== BILLING REQUESTS METHODS ====================

    def _get_all_billing_requests(self):
        """Get all billing requests based on user role"""
        db = get_db_session()
        try:
            if self._is_admin():
                # Admin sees all requests
                requests = db.query(BillingRequest).order_by(
                    BillingRequest.created_at.desc()
                ).limit(100).all()
            else:
                # Employees see only their requests
                employee_id = self._get_employee_id()
                if employee_id:
                    requests = db.query(BillingRequest).filter(
                        BillingRequest.employee_id == employee_id
                    ).order_by(BillingRequest.created_at.desc()).limit(100).all()
                else:
                    requests = []
            return requests
        except Exception as e:
            print(f"Error loading billing requests: {e}")
            return []
        finally:
            db.close()

    def _get_billing_request_summary(self):
        """Get billing request summary"""
        db = get_db_session()
        try:
            from sqlalchemy import func

            query = db.query(BillingRequest)

            # Filter by employee if not admin
            if not self._is_admin():
                employee_id = self._get_employee_id()
                if employee_id:
                    query = query.filter(
                        BillingRequest.employee_id == employee_id)
                else:
                    return {'pending': 0, 'approved': 0, 'rejected': 0, 'total': 0, 'total_amount': 0}

            # Get counts by status
            pending = query.filter(BillingRequest.status == "pending").count()
            approved = query.filter(
                BillingRequest.status == "approved").count()
            rejected = query.filter(
                BillingRequest.status == "rejected").count()
            total = query.count()

            # Get total amount
            total_amount = db.query(func.sum(BillingRequest.bill_amount)).filter(
                BillingRequest.status == "approved"
            ).scalar() or 0

            return {
                'pending': pending,
                'approved': approved,
                'rejected': rejected,
                'total': total,
                'total_amount': float(total_amount)
            }
        except Exception as e:
            print(f"Error getting billing summary: {e}")
            return {'pending': 0, 'approved': 0, 'rejected': 0, 'total': 0, 'total_amount': 0}
        finally:
            db.close()

    def _build_billing_requests_view(self):
        """Build billing requests view"""
        # Summary cards
        summary = self._get_billing_request_summary()

        summary_cards = ft.Container(
            padding=15,
            content=ft.Row([
                self._create_summary_card(
                    "Pending",
                    str(summary['pending']),
                    ft.Icons.PENDING,
                    WARNING
                ),
                self._create_summary_card(
                    "Approved",
                    str(summary['approved']),
                    ft.Icons.CHECK_CIRCLE,
                    GREEN
                ),
                self._create_summary_card(
                    "Rejected",
                    str(summary['rejected']),
                    ft.Icons.CANCEL,
                    ERROR
                ),
                self._create_summary_card(
                    "Total Approved",
                    f"₹{summary['total_amount']:,.2f}",
                    ft.Icons.ATTACH_MONEY,
                    PRIMARY
                ),
            ], spacing=20),
            bgcolor=SURFACE
        )

        # Get requests
        requests = self._get_all_billing_requests()

        if not requests:
            return ft.Column([
                summary_cards,
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.RECEIPT_LONG_OUTLINED,
                                size=64, color="#BDBDBD"),
                        ft.Text("No billing requests yet.",
                                size=14, color="#757575"),
                        ft.Container(height=10),
                        ft.ElevatedButton(
                            "Create First Request",
                            icon=ft.Icons.ADD,
                            on_click=self._show_add_billing_request_dialog,
                            style=ft.ButtonStyle(
                                bgcolor=PRIMARY, color="WHITE")
                        ),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    alignment=ft.alignment.Alignment(0, 0),
                    expand=True
                )
            ], expand=True)

        # Build table rows
        rows = []
        for req in requests:
            # Get employee name
            employee_name = "Unknown"
            try:
                db = get_db_session()
                from database.models import Employee
                emp = db.query(Employee).filter(
                    Employee.id == req.employee_id).first()
                if emp:
                    employee_name = f"{emp.first_name} {emp.last_name}"
                db.close()
            except Exception:
                pass

            status_colors = {
                "pending": WARNING,
                "approved": GREEN,
                "rejected": ERROR,
                "cancelled": TEXT_SECONDARY
            }
            status_color = status_colors.get(req.status, TEXT_SECONDARY)

            # Get attachments count
            attach_count = 0
            try:
                db = get_db_session()
                attach_count = db.query(BillingRequestAttachment).filter(
                    BillingRequestAttachment.billing_request_id == req.id
                ).count()
                db.close()
            except Exception:
                pass

            rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(
                            ft.Text(req.request_number or "-", size=12)),
                        ft.DataCell(ft.Text(employee_name, size=12)),
                        ft.DataCell(ft.Text(req.request_type.replace(
                            "_", " ").title(), size=12)),
                        ft.DataCell(
                            ft.Text(f"₹{req.bill_amount:,.2f}", size=13, weight=ft.FontWeight.BOLD)),
                        ft.DataCell(
                            ft.Text(req.bill_category or "-", size=12)),
                        ft.DataCell(ft.Text(str(req.bill_date), size=11)),
                        ft.DataCell(ft.Container(
                            content=ft.Text(req.status.title(),
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
                                    icon_color=PRIMARY if attach_count > 0 else TEXT_SECONDARY,
                                    tooltip=f"{attach_count} attachments",
                                    scale=0.7,
                                    on_click=lambda e, rid=req.id: self._show_billing_attachments(
                                        rid)
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.VISIBILITY,
                                    icon_color=PRIMARY,
                                    tooltip="View Details",
                                    on_click=lambda e, rid=req.id: self._show_billing_details(
                                        rid),
                                    scale=0.7
                                ),
                                # Show approve/reject buttons only for admin on pending requests
                                ft.IconButton(
                                    icon=ft.Icons.CHECK,
                                    icon_color=GREEN,
                                    tooltip="Approve",
                                    scale=0.7,
                                    visible=self._is_admin() and req.status == "pending",
                                    on_click=lambda e, rid=req.id: self._approve_billing_request(
                                        rid)
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.CLOSE,
                                    icon_color=ERROR,
                                    tooltip="Reject",
                                    scale=0.7,
                                    visible=self._is_admin() and req.status == "pending",
                                    on_click=lambda e, rid=req.id: self._reject_billing_request(
                                        rid)
                                ),
                            ], spacing=0)
                        ),
                    ]
                )
            )

        return ft.Column([
            summary_cards,
            ft.Container(
                padding=20,
                content=ft.Column([
                    ft.Row([
                        ft.Text("Billing Requests", size=18,
                                weight=ft.FontWeight.BOLD),
                        ft.Container(expand=True),
                    ]),
                    ft.Container(height=15),
                    ft.DataTable(
                        columns=[
                            ft.DataColumn(label=ft.Text("Request #")),
                            ft.DataColumn(label=ft.Text("Employee")),
                            ft.DataColumn(label=ft.Text("Type")),
                            ft.DataColumn(label=ft.Text("Amount")),
                            ft.DataColumn(label=ft.Text("Category")),
                            ft.DataColumn(label=ft.Text("Bill Date")),
                            ft.DataColumn(label=ft.Text("Status")),
                            ft.DataColumn(label=ft.Text("Actions")),
                        ],
                        rows=rows,
                        expand=True,
                    ),
                ], scroll=ft.ScrollMode.AUTO),
                expand=True
            )
        ], expand=True)

    def _show_add_billing_request_dialog(self, e=None):
        """Show add billing request dialog with QR attachment option"""
        self._init_file_picker()

        # File path storage
        receipt_file_path = [None]
        qr_file_path = [None]

        # File path inputs (initially empty)
        receipt_path_input = ft.TextField(
            label="Bill Receipt File",
            width=300,
            hint_text="No file selected",
            read_only=True,
            visible=False
        )
        qr_path_input = ft.TextField(
            label="QR Code File",
            width=300,
            hint_text="No file selected",
            read_only=True,
            visible=False
        )

        # Selected file labels
        receipt_file_label = ft.Text(
            "No file selected", size=11, color=TEXT_SECONDARY)
        qr_file_label = ft.Text(
            "No file selected", size=11, color=TEXT_SECONDARY)

        def pick_receipt_file(e):
            """Pick receipt file using file picker"""
            async def pick_and_save():
                try:
                    files = await self._file_picker.pick_files(
                        dialog_title="Choose Bill Receipt file",
                        file_type=ft.FilePickerFileType.ANY,
                    )
                    if files and files[0]:
                        path = files[0].path
                        receipt_file_path[0] = path
                        file_name = files[0].name
                        receipt_file_label.value = f"✓ {file_name}"
                        receipt_file_label.color = SUCCESS
                        receipt_placeholder.visible = False
                        receipt_selected.visible = True
                        self._page.update()
                except Exception as ex:
                    print(f"Error picking file: {ex}")
                    self._show_error(f"Error picking file: {str(ex)}")

            self._page.run_task(pick_and_save)

        def pick_qr_file(e):
            """Pick QR code file using file picker"""
            async def pick_and_save():
                try:
                    files = await self._file_picker.pick_files(
                        dialog_title="Choose QR Code file",
                        file_type=ft.FilePickerFileType.ANY,
                    )
                    if files and files[0]:
                        path = files[0].path
                        qr_file_path[0] = path
                        file_name = files[0].name
                        qr_file_label.value = f"✓ {file_name}"
                        qr_file_label.color = SUCCESS
                        qr_placeholder.visible = False
                        qr_selected.visible = True
                        self._page.update()
                except Exception as ex:
                    print(f"Error picking file: {ex}")
                    self._show_error(f"Error picking file: {str(ex)}")

            self._page.run_task(pick_and_save)

        # Request type
        type_options = [
            ft.dropdown.Option("accommodation", "Accommodation"),
            ft.dropdown.Option("bill_reimbursement", "Bill Reimbursement"),
            ft.dropdown.Option("expense_claim", "Expense Claim"),
            ft.dropdown.Option("other", "Other"),
        ]
        type_dropdown = ft.Dropdown(
            label="Request Type *",
            options=type_options,
            width=250,
            value="bill_reimbursement"
        )

        # Bill category
        category_options = [
            ft.dropdown.Option("Hotel", "Hotel"),
            ft.dropdown.Option("Travel", "Travel"),
            ft.dropdown.Option("Medical", "Medical"),
            ft.dropdown.Option("Office Supplies", "Office Supplies"),
            ft.dropdown.Option("Food", "Food"),
            ft.dropdown.Option("Transport", "Transport"),
            ft.dropdown.Option("Utilities", "Utilities"),
            ft.dropdown.Option("Other", "Other"),
        ]
        category_dropdown = ft.Dropdown(
            label="Bill Category *",
            options=category_options,
            width=250
        )

        amount_field = ft.TextField(
            label="Bill Amount *", width=200)
        description_field = ft.TextField(
            label="Bill Description *", width=400, multiline=True)
        date_field = ft.TextField(
            label="Bill Date (YYYY-MM-DD)", width=200, value=datetime.now().strftime('%Y-%m-%d'))

        # Payment mode with QR attachment option
        payment_mode_options = [
            ft.dropdown.Option("cash", "Cash"),
            ft.dropdown.Option("bank_transfer", "Bank Transfer"),
            ft.dropdown.Option("upi", "UPI"),
            ft.dropdown.Option("cheque", "Cheque"),
            ft.dropdown.Option("qr_code", "QR Code Payment"),
            ft.dropdown.Option("other", "Other"),
        ]
        payment_mode_dropdown = ft.Dropdown(
            label="Preferred Payment Mode *",
            options=payment_mode_options,
            width=250,
            value="bank_transfer"
        )

        payment_details_field = ft.TextField(
            label="Payment Details (Bank Account/UPI ID/QR Code)", width=400)

        # Bill Receipt attachment section - WITH FILE PICKER
        receipt_placeholder = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.RECEIPT_LONG, color=PRIMARY, size=24),
                ft.Text("Attach Bill Receipt / Invoice", size=14,
                        weight=ft.FontWeight.BOLD, color=PRIMARY),
                ft.Container(expand=True),
                ft.ElevatedButton(
                    "Choose File",
                    icon=ft.Icons.UPLOAD_FILE,
                    on_click=pick_receipt_file,
                    style=ft.ButtonStyle(bgcolor=PRIMARY, color="WHITE"),
                    scale=0.8,
                ),
            ], spacing=10),
            bgcolor="#E3F2FD",
            padding=15,
            border_radius=10,
            border=ft.border.all(1, PRIMARY)
        )

        receipt_selected = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.CHECK_CIRCLE, color=SUCCESS, size=24),
                ft.Column([
                    receipt_file_label,
                    ft.Text("Click to change file",
                            size=10, color=TEXT_SECONDARY),
                ], spacing=2),
                ft.Container(expand=True),
                ft.TextButton("Change", on_click=pick_receipt_file),
            ], spacing=10),
            bgcolor="#E8F5E9",
            padding=15,
            border_radius=10,
            border=ft.border.all(2, SUCCESS),
            visible=False
        )

        # QR Code attachment section - WITH FILE PICKER
        qr_placeholder = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.QR_CODE_2, color=PURPLE, size=28),
                ft.Text("Employee Bank QR Code for UPI Payment", size=15,
                        weight=ft.FontWeight.BOLD, color=PURPLE),
                ft.Container(expand=True),
                ft.ElevatedButton(
                    "Choose File",
                    icon=ft.Icons.UPLOAD_FILE,
                    on_click=pick_qr_file,
                    style=ft.ButtonStyle(bgcolor=PURPLE, color="WHITE"),
                    scale=0.8,
                ),
            ], spacing=10),
            bgcolor="#F3E5F5",
            padding=15,
            border_radius=10,
            border=ft.border.all(2, PURPLE)
        )

        qr_selected = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.CHECK_CIRCLE, color=SUCCESS, size=24),
                ft.Column([
                    qr_file_label,
                    ft.Text("Click to change file",
                            size=10, color=TEXT_SECONDARY),
                ], spacing=2),
                ft.Container(expand=True),
                ft.TextButton("Change", on_click=pick_qr_file),
            ], spacing=10),
            bgcolor="#F3E5F5",
            padding=15,
            border_radius=10,
            border=ft.border.all(2, PURPLE),
            visible=False
        )

        error_text = ft.Text("", color=ERROR, size=12, visible=False)

        def save(e):
            if not amount_field.value or not amount_field.value.replace('.', '').isdigit():
                error_text.value = "Valid amount required!"
                error_text.visible = True
                self._page.update()
                return

            if not category_dropdown.value:
                error_text.value = "Category required!"
                error_text.visible = True
                self._page.update()
                return

            if not description_field.value:
                error_text.value = "Description required!"
                error_text.visible = True
                self._page.update()
                return

            try:
                bill_date = datetime.strptime(
                    date_field.value, '%Y-%m-%d').date()
            except Exception:
                bill_date = date.today()

            employee_id = self._get_employee_id()
            if not employee_id:
                error_text.value = "Employee not found. Please login again."
                error_text.visible = True
                self._page.update()
                return

            # Generate request number
            request_number = f"BR-{datetime.now().strftime('%Y%m%d%H%M%S')}"

            db = get_db_session()
            try:
                new_request = BillingRequest(
                    request_number=request_number,
                    request_type=type_dropdown.value,
                    employee_id=employee_id,
                    bill_description=description_field.value,
                    bill_amount=float(amount_field.value),
                    bill_date=bill_date,
                    bill_category=category_dropdown.value,
                    payment_mode=payment_mode_dropdown.value,
                    payment_details=payment_details_field.value or None,
                    status="pending"
                )
                db.add(new_request)
                db.flush()  # Get the request ID

                # Save receipt attachment if provided
                if receipt_file_path[0] and os.path.exists(receipt_file_path[0]):
                    try:
                        file_size = os.path.getsize(receipt_file_path[0])
                        if file_size <= MAX_FILE_SIZE:
                            file_name = os.path.basename(receipt_file_path[0])
                            file_ext = os.path.splitext(
                                file_name)[1].lower().replace('.', '')
                            att = BillingRequestAttachment(
                                billing_request_id=new_request.id,
                                file_path=receipt_file_path[0],
                                file_name=file_name,
                                file_size=file_size,
                                file_type=file_ext,
                                attachment_type="receipt",
                                uploaded_by_id=self._get_user_id()
                            )
                            db.add(att)
                    except Exception as att_err:
                        print(f"Error saving receipt attachment: {att_err}")

                # Save QR code attachment if provided
                if qr_file_path[0] and os.path.exists(qr_file_path[0]):
                    try:
                        file_size = os.path.getsize(qr_file_path[0])
                        if file_size <= MAX_FILE_SIZE:
                            file_name = os.path.basename(qr_file_path[0])
                            file_ext = os.path.splitext(
                                file_name)[1].lower().replace('.', '')
                            att = BillingRequestAttachment(
                                billing_request_id=new_request.id,
                                file_path=qr_file_path[0],
                                file_name=file_name,
                                file_size=file_size,
                                file_type=file_ext,
                                attachment_type="qr_code",
                                uploaded_by_id=self._get_user_id()
                            )
                            db.add(att)
                    except Exception as att_err:
                        print(f"Error saving QR attachment: {att_err}")

                db.commit()

                self._show_success(
                    "Billing request submitted with attachments!")
                self._close_dialog()
                self._refresh()
            except Exception as ex:
                error_text.value = f"Error: {str(ex)}"
                error_text.visible = True
                self._page.update()
            finally:
                db.close()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("New Bill Reimbursement Request"),
            content=ft.Container(
                content=ft.Column([
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Icon(ft.Icons.RECEIPT,
                                        color="WHITE", size=20),
                                ft.Text("Bill Reimbursement", size=16,
                                        weight=ft.FontWeight.BOLD, color="WHITE"),
                            ], spacing=10),
                            ft.Text("Submit your bill for reimbursement with receipt and payment details",
                                    size=11, color="WHITE"),
                        ], spacing=5),
                        bgcolor=PRIMARY,
                        padding=15,
                        border_radius=10,
                    ),
                    ft.Divider(),
                    ft.Text("Bill Details", size=14,
                            weight=ft.FontWeight.BOLD),
                    type_dropdown,
                    category_dropdown,
                    amount_field,
                    description_field,
                    ft.Row([date_field], spacing=10),
                    ft.Divider(),
                    ft.Text("Required Attachments", size=14,
                            weight=ft.FontWeight.BOLD),
                    # Bill Receipt with file picker
                    receipt_placeholder,
                    receipt_selected,
                    ft.Container(height=10),
                    # QR Code with file picker
                    qr_placeholder,
                    qr_selected,
                    ft.Divider(),
                    ft.Text("Payment Information", size=14,
                            weight=ft.FontWeight.BOLD),
                    payment_mode_dropdown,
                    payment_details_field,
                    error_text,
                ], spacing=10, scroll=ft.ScrollMode.AUTO),
                width=520,
            ),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda e: self._close_dialog()),
                ft.ElevatedButton("Submit Request", on_click=save, style=ft.ButtonStyle(
                    bgcolor=SUCCESS, color="WHITE")),
            ]
        )

        self._page.overlay.append(dialog)
        dialog.open = True
        self._page.update()

    def _show_billing_details(self, request_id):
        """Show billing request details with options to add attachments, view QR code, and make payment for admin"""
        db = get_db_session()
        try:
            req = db.query(BillingRequest).filter(
                BillingRequest.id == request_id).first()
            if not req:
                self._show_error("Request not found")
                return

            # Get employee name
            employee_name = "Unknown"
            from database.models import Employee
            emp = db.query(Employee).filter(
                Employee.id == req.employee_id).first()
            if emp:
                employee_name = f"{emp.first_name} {emp.last_name}"

            # Get attachments
            attachments = db.query(BillingRequestAttachment).filter(
                BillingRequestAttachment.billing_request_id == request_id
            ).all()

        except Exception as e:
            self._show_error(f"Error: {str(e)}")
            return
        finally:
            db.close()

        # Separate receipt and QR code attachments
        receipt_attachments = [
            a for a in attachments if a.attachment_type == "receipt"]
        qr_attachments = [
            a for a in attachments if a.attachment_type == "qr_code"]

        # Build attachments list with type indicators, preview and download buttons for admin
        attach_list = ft.Column()

        # Receipt section
        attach_list.controls.append(
            ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.RECEIPT, size=20, color=PRIMARY),
                    ft.Text("Receipt/Bill", size=13,
                            weight=ft.FontWeight.BOLD),
                ], spacing=10),
                margin=ft.margin.only(bottom=5),
            )
        )

        if receipt_attachments:
            for att in receipt_attachments:
                size_kb = att.file_size / 1024 if att.file_size else 0
                # Admin download button
                download_btn = ft.IconButton(
                    icon=ft.Icons.DOWNLOAD,
                    icon_color=SUCCESS,
                    tooltip="Download Receipt",
                    scale=0.7,
                    on_click=lambda e, a=att: self._download_attachment(
                        a.file_path, a.file_name)
                ) if self._is_admin() else ft.Container()

                # Preview button
                preview_btn = ft.IconButton(
                    icon=ft.Icons.VISIBILITY,
                    icon_color=INFO,
                    tooltip="Preview",
                    scale=0.7,
                    on_click=lambda e, a=att: self._preview_billing_attachment(
                        a)
                )

                attach_list.controls.append(
                    ft.Container(
                        padding=10,
                        bgcolor="#F5F5F5",
                        border_radius=8,
                        margin=ft.margin.only(bottom=5),
                        content=ft.Row([
                            ft.Icon(ft.Icons.ATTACHMENT, size=16,
                                    color=TEXT_SECONDARY),
                            ft.Text(att.file_name or "Unknown",
                                    expand=True, size=12),
                            ft.Text(f"{size_kb:.1f} KB", size=10,
                                    color=TEXT_SECONDARY),
                            preview_btn,
                            download_btn,
                        ], spacing=10)
                    )
                )
        else:
            attach_list.controls.append(
                ft.Container(
                    content=ft.Text("No receipt attached", size=11,
                                    color=TEXT_SECONDARY, italic=True),
                    padding=5,
                    margin=ft.margin.only(bottom=5),
                )
            )

        # QR display - always define this regardless of receipt attachments
        if qr_attachments:
            # Build QR items list first
            qr_items = []
            for att in qr_attachments:
                qr_items.append(
                    ft.Container(
                        padding=15,
                        bgcolor="#F3E5F5",
                        border_radius=10,
                        border=ft.border.all(2, PURPLE),
                        content=ft.Column([
                            ft.Row([
                                ft.Icon(ft.Icons.QR_CODE,
                                        size=24, color=PURPLE),
                                ft.Text(att.file_name, size=12,
                                        weight=ft.FontWeight.BOLD),
                                ft.Container(expand=True),
                                ft.Text(f"{att.file_size/1024:.1f} KB",
                                        size=10, color=TEXT_SECONDARY),
                            ], spacing=10),
                            ft.Container(height=8),
                            ft.Row([
                                ft.ElevatedButton(
                                    "Preview",
                                    icon=ft.Icons.VISIBILITY,
                                    on_click=lambda e, a=att: self._preview_billing_attachment(
                                        a),
                                    style=ft.ButtonStyle(
                                        bgcolor=INFO, color="WHITE"),
                                    scale=0.8,
                                ),
                                ft.ElevatedButton(
                                    "Download QR",
                                    icon=ft.Icons.DOWNLOAD,
                                    on_click=lambda e, a=att: self._download_attachment(
                                        a.file_path, a.file_name),
                                    style=ft.ButtonStyle(
                                        bgcolor=PRIMARY, color="WHITE"),
                                    scale=0.8,
                                ),
                            ], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
                    )
                )
                qr_items.append(ft.Container(height=10))

            qr_display = ft.Container(
                content=ft.Column([
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.QR_CODE_2,
                                    size=28, color=PURPLE),
                            ft.Text("Employee's Bank QR Code", size=15,
                                    weight=ft.FontWeight.BOLD, color=PURPLE),
                        ], spacing=10),
                        padding=10,
                        bgcolor=PURPLE,
                        border_radius=10,
                    ),
                    ft.Container(height=10),
                    ft.Column(qr_items, spacing=5),
                ], spacing=5),
                padding=10,
                bgcolor="#FAFAFA",
                border_radius=10,
            )
        else:
            qr_display = ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.QR_CODE_2, size=20,
                                color=TEXT_SECONDARY),
                        ft.Text("No QR Code Attached", size=12,
                                color=TEXT_SECONDARY, italic=True),
                    ], spacing=5),
                ], spacing=2),
                padding=10,
                bgcolor="#F5F5F5",
                border_radius=8,
            )

        # Status badge with color
        status_colors = {
            "pending": WARNING,
            "approved": GREEN,
            "rejected": ERROR,
        }
        status_color = status_colors.get(req.status, TEXT_SECONDARY)

        # Admin QR Scan & Pay section
        admin_payment_section = ft.Container()
        if self._is_admin() and qr_attachments and req.status == "approved":
            def open_payment_dialog(e):
                self._close_dialog()
                self._show_payment_dialog(request_id)

            admin_payment_section = ft.Container(
                content=ft.Column([
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.PHONE_ANDROID,
                                    size=24, color="WHITE"),
                            ft.Text("Scan QR & Make Payment", size=15,
                                    weight=ft.FontWeight.BOLD, color="WHITE"),
                        ], spacing=10, alignment=ft.MainAxisAlignment.CENTER),
                        padding=15,
                        bgcolor=GREEN,
                        border_radius=10,
                    ),
                    ft.Container(height=10),
                    ft.Text("1. Download or view the QR code above",
                            size=11, color=TEXT_SECONDARY),
                    ft.Text("2. Scan with your phone's UPI app to pay",
                            size=11, color=TEXT_SECONDARY),
                    ft.Text("3. Click below to confirm payment",
                            size=11, color=TEXT_SECONDARY),
                    ft.Container(height=10),
                    ft.ElevatedButton(
                        "Confirm Payment Made",
                        icon=ft.Icons.CHECK_CIRCLE,
                        on_click=open_payment_dialog,
                        style=ft.ButtonStyle(
                            bgcolor=SUCCESS, color="WHITE", padding=20),
                    ),
                ], spacing=8, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=15,
                bgcolor="#E8F5E9",
                border_radius=10,
                border=ft.border.all(2, GREEN),
            )

        # Add attachment buttons
        def add_receipt(e):
            self._close_dialog()
            self._show_add_billing_attachment_dialog(request_id, "receipt")

        def add_qr(e):
            self._close_dialog()
            self._show_add_billing_attachment_dialog(request_id, "qr_code")

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Request #{req.request_number}"),
            content=ft.Container(
                content=ft.Column([
                    # Request info section
                    ft.Container(
                        padding=15,
                        bgcolor="#F8F9FA",
                        border_radius=10,
                        content=ft.Column([
                            ft.Row([
                                ft.Column([
                                    ft.Text("Employee", size=10,
                                            color=TEXT_SECONDARY),
                                    ft.Text(employee_name, size=13,
                                            weight=ft.FontWeight.BOLD),
                                ], spacing=2, expand=True),
                                ft.Container(
                                    content=ft.Text(
                                        req.status.upper(), size=11, color="WHITE"),
                                    bgcolor=status_color,
                                    padding=ft.padding.symmetric(
                                        horizontal=10, vertical=4),
                                    border_radius=12,
                                ),
                            ], spacing=10),
                            ft.Divider(height=15),
                            ft.Row([
                                ft.Column([
                                    ft.Text("Amount", size=10,
                                            color=TEXT_SECONDARY),
                                    ft.Text(
                                        f"₹{req.bill_amount:,.2f}", size=16, weight=ft.FontWeight.BOLD, color=GREEN),
                                ], spacing=2),
                                ft.Column([
                                    ft.Text("Type", size=10,
                                            color=TEXT_SECONDARY),
                                    ft.Text(req.request_type.replace(
                                        "_", " ").title(), size=12),
                                ], spacing=2),
                                ft.Column([
                                    ft.Text("Category", size=10,
                                            color=TEXT_SECONDARY),
                                    ft.Text(req.bill_category or "-", size=12),
                                ], spacing=2),
                            ], spacing=20),
                            ft.Divider(height=15),
                            ft.Row([
                                ft.Column([
                                    ft.Text("Bill Date", size=10,
                                            color=TEXT_SECONDARY),
                                    ft.Text(str(req.bill_date), size=12),
                                ], spacing=2),
                                ft.Column([
                                    ft.Text("Payment Mode", size=10,
                                            color=TEXT_SECONDARY),
                                    ft.Text(req.payment_mode.replace(
                                        "_", " ").title(), size=12),
                                ], spacing=2, expand=True),
                            ], spacing=20),
                            ft.Container(height=5),
                            ft.Text(
                                f"Payment Details: {req.payment_details or 'N/A'}", size=11, color=TEXT_SECONDARY),
                        ], spacing=5),
                    ),
                    ft.Divider(),
                    ft.Text("Description:", size=12,
                            weight=ft.FontWeight.BOLD),
                    ft.Container(
                        content=ft.Text(
                            req.bill_description or "No description", size=11),
                        padding=10,
                        bgcolor="#FFFDE7",
                        border_radius=8,
                    ),
                    ft.Divider(),
                    ft.Text("Attachments:", size=12,
                            weight=ft.FontWeight.BOLD),
                    attach_list,
                    ft.Container(height=10),
                    # QR Code Display Section (Prominent for Admin)
                    ft.Container(
                        content=ft.Column([
                            ft.Text("Bank QR Code for Payment", size=13,
                                    weight=ft.FontWeight.BOLD),
                            qr_display,
                        ], spacing=5),
                    ),
                    ft.Container(height=10),
                    # Admin Payment Section
                    admin_payment_section,
                    ft.Container(height=10),
                    # Add Receipt and QR Code buttons
                    ft.Row([
                        ft.ElevatedButton(
                            "Add Receipt",
                            icon=ft.Icons.RECEIPT,
                            on_click=add_receipt,
                            style=ft.ButtonStyle(
                                bgcolor=PRIMARY, color="WHITE"),
                            scale=0.9,
                        ),
                        ft.ElevatedButton(
                            "Add QR Code",
                            icon=ft.Icons.QR_CODE,
                            on_click=add_qr,
                            style=ft.ButtonStyle(
                                bgcolor=PURPLE, color="WHITE"),
                            scale=0.9,
                        ),
                    ], spacing=10, alignment=ft.MainAxisAlignment.CENTER),
                ], spacing=5, scroll=ft.ScrollMode.AUTO),
                width=500,
                height=650,
            ),
            actions=[
                ft.TextButton(
                    "Close", on_click=lambda e: self._close_dialog()),
            ]
        )

        self._page.overlay.append(dialog)
        dialog.open = True
        self._page.update()

    def _show_payment_dialog(self, request_id):
        """Show dialog to confirm payment was made"""
        payment_ref_field = ft.TextField(
            label="Payment Reference (Transaction ID)", width=350)
        notes_field = ft.TextField(
            label="Payment Notes (Optional)", width=350, multiline=True)

        def confirm_payment(e):
            db = get_db_session()
            try:
                req = db.query(BillingRequest).filter(
                    BillingRequest.id == request_id).first()
                if req:
                    # Add payment notes
                    payment_notes = f"Payment confirmed via QR scan. "
                    if payment_ref_field.value:
                        payment_notes += f"Ref: {payment_ref_field.value}. "
                    if notes_field.value:
                        payment_notes += notes_field.value

                    if req.notes:
                        req.notes = req.notes + "\n" + payment_notes
                    else:
                        req.notes = payment_notes

                    db.commit()
                    self._show_success(
                        "Payment confirmed! The request has been marked as paid.")
                    self._close_dialog()
                    self._refresh()
            except Exception as ex:
                self._show_error(f"Error: {str(ex)}")
            finally:
                db.close()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirm Payment", color=SUCCESS),
            content=ft.Column([
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.CHECK_CIRCLE,
                                    color=SUCCESS, size=32),
                            ft.Text("Confirm Payment Made", size=16,
                                    weight=ft.FontWeight.BOLD),
                        ], spacing=10),
                        ft.Text("After scanning the QR code and making the payment, confirm it here:",
                                size=11, color=TEXT_SECONDARY),
                    ], spacing=10),
                    bgcolor="#E8F5E9",
                    padding=15,
                    border_radius=10,
                ),
                ft.Container(height=15),
                payment_ref_field,
                notes_field,
                ft.Container(height=10),
                ft.Text("This will update the request status and add payment notes.",
                        size=10, color=TEXT_SECONDARY, italic=True),
            ], spacing=10),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda e: self._close_dialog()),
                ft.ElevatedButton("Confirm Payment", on_click=confirm_payment,
                                  style=ft.ButtonStyle(bgcolor=SUCCESS, color="WHITE")),
            ]
        )

    def _download_attachment(self, file_path, file_name, file_data=None):
        """Download attachment file - supports Supabase URLs, file path, and database binary data"""
        # First try to use binary data from database if available
        if file_data:
            try:
                import shutil
                download_dir = os.path.expanduser("~/Downloads")
                os.makedirs(download_dir, exist_ok=True)
                dest_path = os.path.join(download_dir, file_name)
                with open(dest_path, 'wb') as f:
                    f.write(file_data)
                self._show_success(f"Downloaded: {dest_path}")
                return
            except Exception as e:
                self._show_error(f"Download from database failed: {str(e)}")
                # Continue to try other methods

        # Check if file_path is a Supabase URL
        if file_path and file_path.startswith('http'):
            try:
                import requests
                download_dir = os.path.expanduser("~/Downloads")
                os.makedirs(download_dir, exist_ok=True)
                dest_path = os.path.join(download_dir, file_name)

                # Download from Supabase URL
                response = requests.get(file_path, timeout=30)
                if response.status_code == 200:
                    with open(dest_path, 'wb') as f:
                        f.write(response.content)
                    self._show_success(f"Downloaded from cloud: {dest_path}")
                else:
                    self._show_error(
                        f"Download failed: HTTP {response.status_code}")
                return
            except Exception as e:
                self._show_error(f"Cloud download failed: {str(e)}")
                return

        # Fall back to local file path
        if not file_path:
            self._show_error("File path not found")
            return

        if not os.path.exists(file_path):
            self._show_error(f"File not found: {file_path}")
            return

        try:
            # Copy to Downloads folder
            import shutil
            download_dir = os.path.expanduser("~/Downloads")
            os.makedirs(download_dir, exist_ok=True)
            dest_path = os.path.join(download_dir, file_name)
            shutil.copy2(file_path, dest_path)
            self._show_success(f"Downloaded: {dest_path}")
        except Exception as e:
            self._show_error(f"Download failed: {str(e)}")

    def _show_add_billing_attachment_dialog(self, request_id, attachment_type="receipt"):
        """Show dialog to add receipt or QR code attachment - uploads to Supabase Cloud Storage"""
        self._init_file_picker()

        type_label = "Receipt" if attachment_type == "receipt" else "QR Code"
        type_icon = ft.Icons.RECEIPT if attachment_type == "receipt" else ft.Icons.QR_CODE

        file_path = [None]

        def pick_file(e):
            async def pick_and_save():
                try:
                    files = await self._file_picker.pick_files(
                        dialog_title=f"Choose {type_label} file",
                        file_type=ft.FilePickerFileType.ANY,
                    )
                    if files and files[0]:
                        path = files[0].path
                        file_path[0] = path
                        path_input.value = path
                        self._page.update()
                except Exception as ex:
                    print(f"Error picking file: {ex}")

            self._page.run_task(pick_and_save)

        path_input = ft.TextField(
            label=f"{type_label} File Path", width=350,
            hint_text="Enter full path to file or browse")

        browse_btn = ft.ElevatedButton(
            "Browse",
            icon=ft.Icons.FOLDER_OPEN,
            on_click=pick_file,
            style=ft.ButtonStyle(bgcolor=PRIMARY, color="WHITE")
        )

        # Status indicator
        upload_status = ft.Text("", size=11, color=TEXT_SECONDARY)

        def save_attachment(e):
            if not path_input.value:
                self._show_error("File path required")
                return

            if not os.path.exists(path_input.value):
                self._show_error("File not found")
                return

            file_size = os.path.getsize(path_input.value)
            if file_size > MAX_FILE_SIZE:
                self._show_error(
                    f"File too large! Max {MAX_UPLOAD_SIZE_MB}MB allowed (yours: {file_size/1024/1024:.1f}MB)")
                return

            file_name = os.path.basename(path_input.value)
            file_ext = os.path.splitext(file_name)[1].lower().replace('.', '')

            # Show uploading status
            upload_status.value = "Uploading to cloud..."
            upload_status.color = INFO
            self._page.update()

            # Try to upload to Supabase Cloud Storage
            file_url = None
            upload_success = False
            upload_error = None
            local_file_data = None

            try:
                storage = get_storage()
                if storage.available:
                    # Upload to Supabase Storage
                    folder = "billing_receipts" if attachment_type == "receipt" else "billing_qr_codes"
                    success, url_or_error, bucket_path = upload_to_supabase(
                        path_input.value,
                        folder=folder,
                        custom_filename=f"bill_{request_id}_{attachment_type}_{int(datetime.now().timestamp())}_{file_name}"
                    )

                    if success and url_or_error:
                        file_url = url_or_error
                        upload_success = True
                        print(
                            f"[Billing] {type_label} uploaded to Supabase: {file_url}")
                    else:
                        upload_error = url_or_error
                        print(
                            f"[Billing] Supabase upload failed: {url_or_error}")
                else:
                    upload_error = "Cloud storage not configured"
                    print("[Billing] Supabase storage not available")
            except Exception as upload_err:
                upload_error = str(upload_err)
                print(f"[Billing] Upload error: {upload_err}")

            # If Supabase upload failed or not available, fall back to local storage
            if not upload_success:
                if upload_error:
                    upload_status.value = f"Cloud upload failed: {upload_error}. Saving locally."
                    upload_status.color = WARNING
                    self._page.update()

                try:
                    with open(path_input.value, 'rb') as f:
                        local_file_data = f.read()
                    file_url = path_input.value  # Store local path as fallback
                except Exception as e:
                    self._show_error(f"Error reading file: {str(e)}")
                    return
            else:
                upload_status.value = "Uploaded to cloud!"
                upload_status.color = SUCCESS

            db = get_db_session()
            try:
                att = BillingRequestAttachment(
                    billing_request_id=request_id,
                    file_path=file_url,  # Store Supabase URL or local path
                    file_name=file_name,
                    file_size=file_size,
                    file_type=file_ext,
                    file_data=local_file_data,  # Keep local backup if available
                    attachment_type=attachment_type,
                    uploaded_by_id=self._get_user_id()
                )
                db.add(att)
                db.commit()

                self._show_success(
                    f"{type_label} uploaded to cloud!" if upload_success else f"{type_label} uploaded successfully!")
                self._close_dialog()
                # Refresh to show new attachment
                self._refresh()
            except Exception as ex:
                self._show_error(f"Error: {str(ex)}")
            finally:
                db.close()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Add {type_label}"),
            content=ft.Column([
                ft.Container(
                    content=ft.Row([
                        ft.Icon(type_icon, color=PRIMARY, size=24),
                        ft.Text(
                            f"Upload {type_label} for this billing request", size=12, color=TEXT_SECONDARY),
                    ], spacing=10),
                    padding=10,
                ),
                ft.Text(f"Max file size: {MAX_UPLOAD_SIZE_MB}MB",
                        size=11, color=TEXT_SECONDARY),
                ft.Text(
                    "Files are uploaded to cloud storage for easy access", size=10, color=SUCCESS),
                ft.Row([path_input, browse_btn], spacing=10),
                upload_status,
            ], spacing=10),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda e: self._close_dialog()),
                ft.ElevatedButton("Upload", on_click=save_attachment, style=ft.ButtonStyle(
                    bgcolor=SUCCESS, color="WHITE")),
            ]
        )

        self._page.overlay.append(dialog)
        dialog.open = True
        self._page.update()

    def _build_qr_display(self, attachment):
        """Build inline QR code display with image preview"""
        # Try to get image source
        img_src = None
        file_ext = ""

        if attachment.file_name:
            file_ext = attachment.file_name.split(
                '.')[-1].lower() if '.' in attachment.file_name else ""

        image_extensions = ['jpg', 'jpeg', 'png', 'gif', 'webp']

        try:
            # Check if we have binary data in database
            if hasattr(attachment, 'file_data') and attachment.file_data:
                import base64
                img_bytes = attachment.file_data
                b64_str = base64.b64encode(img_bytes).decode()
                img_src = f"data:image/{file_ext};base64,{b64_str}"
            elif attachment.file_path and os.path.exists(attachment.file_path):
                img_src = attachment.file_path
        except Exception as e:
            print(f"Error getting QR image: {e}")

        # Build the display container
        if img_src and file_ext in image_extensions:
            # Show inline image
            return ft.Container(
                padding=15,
                bgcolor="#F3E5F5",
                border_radius=10,
                border=ft.border.all(2, PURPLE),
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.QR_CODE, size=24, color=PURPLE),
                        ft.Text(attachment.file_name or "QR Code",
                                size=12, weight=ft.FontWeight.BOLD),
                        ft.Container(expand=True),
                        ft.Text(f"{(attachment.file_size or 0)/1024:.1f} KB",
                                size=10, color=TEXT_SECONDARY),
                    ], spacing=10),
                    ft.Container(height=10),
                    # Show the QR image inline
                    ft.Container(
                        content=ft.Image(
                            src=img_src,
                            width=200,
                            height=200,
                            fit="contain",
                        ),
                        alignment=ft.alignment.Alignment(0, 0),
                        padding=10,
                        bgcolor="white",
                        border_radius=8,
                    ),
                    ft.Container(height=10),
                    ft.Row([
                        ft.ElevatedButton(
                            "Download QR",
                            icon=ft.Icons.DOWNLOAD,
                            on_click=lambda e, a=attachment: self._download_attachment(
                                a.file_path, a.file_name, a.file_data if hasattr(a, 'file_data') else None),
                            style=ft.ButtonStyle(
                                bgcolor=PRIMARY, color="WHITE"),
                            scale=0.8,
                        ),
                    ], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
            )
        else:
            # No image available - show file info
            return ft.Container(
                padding=15,
                bgcolor="#F3E5F5",
                border_radius=10,
                border=ft.border.all(2, PURPLE),
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.QR_CODE, size=24, color=PURPLE),
                        ft.Text(attachment.file_name or "QR Code",
                                size=12, weight=ft.FontWeight.BOLD),
                        ft.Container(expand=True),
                        ft.Text(f"{(attachment.file_size or 0)/1024:.1f} KB",
                                size=10, color=TEXT_SECONDARY),
                    ], spacing=10),
                    ft.Container(height=10),
                    ft.Text("QR image not available for preview",
                            size=11, color=TEXT_SECONDARY),
                    ft.Container(height=10),
                    ft.Row([
                        ft.ElevatedButton(
                            "Download QR",
                            icon=ft.Icons.DOWNLOAD,
                            on_click=lambda e, a=attachment: self._download_attachment(
                                a.file_path, a.file_name),
                            style=ft.ButtonStyle(
                                bgcolor=PRIMARY, color="WHITE"),
                            scale=0.8,
                        ),
                    ], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
            )

    def _show_billing_attachments(self, request_id):
        """Show attachments for a billing request"""
        self._show_billing_details(request_id)

    def _preview_billing_attachment(self, attachment):
        """Preview a billing request attachment file - supports Supabase URLs, file path, and database binary data"""
        if not attachment:
            self._show_error("Attachment not found")
            return

        # Determine file type
        file_ext = ""
        if attachment.file_name:
            file_ext = attachment.file_name.split(
                '.')[-1].lower() if '.' in attachment.file_name else ""

        # Check if it's an image
        image_extensions = ['jpg', 'jpeg', 'png', 'gif', 'webp']

        if file_ext in image_extensions:
            # Show image preview - try Supabase URL first, then database, then file path
            img_src = None
            try:
                # Check if file_path is a Supabase URL
                if attachment.file_path and attachment.file_path.startswith('http'):
                    # Use Supabase URL directly
                    img_src = attachment.file_path
                # Check if we have binary data in database
                elif hasattr(attachment, 'file_data') and attachment.file_data:
                    # Use base64 encoded data from database
                    import base64
                    img_bytes = attachment.file_data
                    b64_str = base64.b64encode(img_bytes).decode()
                    img_src = f"data:image/{file_ext};base64,{b64_str}"
                elif attachment.file_path and os.path.exists(attachment.file_path):
                    # Fall back to local file path
                    img_src = attachment.file_path

                if not img_src:
                    self._show_error("File not found")
                    return

                dialog = ft.AlertDialog(
                    modal=True,
                    title=ft.Text(f"Preview: {attachment.file_name}"),
                    content=ft.Container(
                        content=ft.Image(
                            src=img_src,
                            width=400,
                            height=400,
                            fit="contain",
                        ),
                        width=420,
                        height=420,
                    ),
                    actions=[
                        ft.TextButton(
                            "Close", on_click=lambda e: self._close_dialog()),
                        ft.ElevatedButton(
                            "Download",
                            icon=ft.Icons.DOWNLOAD,
                            on_click=lambda e: self._download_attachment(
                                attachment.file_path, attachment.file_name, attachment.file_data if hasattr(attachment, 'file_data') else None),
                            style=ft.ButtonStyle(
                                bgcolor=PRIMARY, color="WHITE")
                        ),
                    ]
                )
                self._page.overlay.append(dialog)
                dialog.open = True
                self._page.update()
            except Exception as e:
                self._show_error(f"Error previewing image: {str(e)}")
        else:
            # For non-image files, just show info and offer download
            size_kb = attachment.file_size / 1024 if attachment.file_size else 0
            # Check if it's a cloud file
            is_cloud = attachment.file_path and attachment.file_path.startswith(
                'http')
            source_text = "Cloud Storage" if is_cloud else "Local"

            dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text(f"File Info: {attachment.file_name}"),
                content=ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.INFO_OUTLINE, size=48, color=INFO),
                        ft.Container(height=10),
                        ft.Text(attachment.file_name, size=14,
                                weight=ft.FontWeight.BOLD),
                        ft.Text(f"Size: {size_kb:.1f} KB",
                                size=12, color=TEXT_SECONDARY),
                        ft.Text(f"Type: {file_ext.upper()}",
                                size=12, color=TEXT_SECONDARY),
                        ft.Text(f"Source: {source_text}",
                                size=11, color=SUCCESS if is_cloud else TEXT_SECONDARY),
                        ft.Container(height=10),
                        ft.Text("Preview not available for this file type.",
                                size=11, color=TEXT_SECONDARY),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=20,
                ),
                actions=[
                    ft.TextButton(
                        "Close", on_click=lambda e: self._close_dialog()),
                    ft.ElevatedButton(
                        "Download",
                        icon=ft.Icons.DOWNLOAD,
                        on_click=lambda e: self._download_attachment(
                            attachment.file_path, attachment.file_name, attachment.file_data if hasattr(attachment, 'file_data') else None),
                        style=ft.ButtonStyle(bgcolor=PRIMARY, color="WHITE")
                    ),
                ]
            )
            self._page.overlay.append(dialog)
            dialog.open = True
            self._page.update()

    def _approve_billing_request(self, request_id):
        """Approve a billing request"""
        def confirm(e):
            db = get_db_session()
            try:
                req = db.query(BillingRequest).filter(
                    BillingRequest.id == request_id).first()
                if req:
                    req.status = "approved"
                    req.reviewed_by_id = self._get_user_id()
                    req.reviewed_at = datetime.utcnow()
                    db.commit()
                    self._show_success("Request approved!")
                    self._close_dialog()
                    self._refresh()
            except Exception as ex:
                self._show_error(f"Error: {str(ex)}")
            finally:
                db.close()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Approve Request?", color=SUCCESS),
            content=ft.Text(
                "Are you sure you want to approve this billing request?"),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda e: self._close_dialog()),
                ft.ElevatedButton("Approve", on_click=confirm, style=ft.ButtonStyle(
                    bgcolor=SUCCESS, color="WHITE")),
            ]
        )

        self._page.overlay.append(dialog)
        dialog.open = True
        self._page.update()

    def _reject_billing_request(self, request_id):
        """Reject a billing request"""
        reason_field = ft.TextField(
            label="Rejection Reason", width=350, multiline=True)

        def confirm(e):
            db = get_db_session()
            try:
                req = db.query(BillingRequest).filter(
                    BillingRequest.id == request_id).first()
                if req:
                    req.status = "rejected"
                    req.reviewed_by_id = self._get_user_id()
                    req.reviewed_at = datetime.utcnow()
                    req.review_notes = reason_field.value or None
                    db.commit()
                    self._show_success("Request rejected!")
                    self._close_dialog()
                    self._refresh()
            except Exception as ex:
                self._show_error(f"Error: {str(ex)}")
            finally:
                db.close()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Reject Request?", color=ERROR),
            content=ft.Column([
                ft.Text("Please provide a reason for rejection:"),
                reason_field,
            ], spacing=10),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda e: self._close_dialog()),
                ft.ElevatedButton("Reject", on_click=confirm, style=ft.ButtonStyle(
                    bgcolor=ERROR, color="WHITE")),
            ]
        )

        self._page.overlay.append(dialog)
        dialog.open = True
        self._page.update()


def show_transactions(page, user):
    """Helper function to show transactions screen"""
    page.clean()
    page.add(TransactionsScreen(page, user))
