from django.contrib import admin
from django.utils.html import format_html
from decimal import Decimal
from .models import Wallet, WalletTransaction
from .services import credit_wallet, apply_wallet_payment


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'balance_display', 'transaction_count', 'created_date')
    search_fields = ('user__email', 'user__full_name')
    readonly_fields = ('user', 'balance', 'created_at', 'updated_at', 'transaction_history')
    list_filter = ('created_at',)
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User'
    
    def balance_display(self, obj):
        color = 'green' if obj.balance > 0 else 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">₹{:,.2f}</span>',
            color,
            obj.balance
        )
    balance_display.short_description = 'Balance'
    
    def transaction_count(self, obj):
        return obj.transactions.count()
    transaction_count.short_description = 'Transactions'
    
    def created_date(self, obj):
        return obj.created_at.strftime('%Y-%m-%d %H:%M')
    created_date.short_description = 'Created'
    
    def transaction_history(self, obj):
        """Display recent transactions."""
        transactions = obj.transactions.all()[:10]
        html = '<table style="width:100%; border-collapse: collapse;">'
        html += '<tr><th style="border: 1px solid #ddd; padding: 8px;">Date</th>'
        html += '<th style="border: 1px solid #ddd; padding: 8px;">Type</th>'
        html += '<th style="border: 1px solid #ddd; padding: 8px;">Amount</th>'
        html += '<th style="border: 1px solid #ddd; padding: 8px;">Status</th></tr>'
        
        for txn in transactions:
            color = 'green' if txn.transaction_type == 'credit' else 'red'
            html += f'<tr><td style="border: 1px solid #ddd; padding: 8px;">{txn.created_at.strftime("%Y-%m-%d %H:%M")}</td>'
            html += f'<td style="border: 1px solid #ddd; padding: 8px;">{txn.get_transaction_type_display()}</td>'
            html += f'<td style="border: 1px solid #ddd; padding: 8px; color: {color}; font-weight: bold;">₹{txn.amount}</td>'
            html += f'<td style="border: 1px solid #ddd; padding: 8px;">{txn.get_status_display()}</td></tr>'
        
        html += '</table>'
        return format_html(html)
    transaction_history.short_description = 'Recent Transactions'


@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = (
        'user_email',
        'transaction_type_badge',
        'amount_display',
        'status_badge',
        'reference_id',
        'transaction_date'
    )
    list_filter = ('transaction_type', 'status', 'created_at')
    search_fields = ('wallet__user__email', 'reference_id', 'description')
    readonly_fields = ('wallet', 'amount', 'transaction_type', 'created_at', 'updated_at')
    fieldsets = (
        ('Transaction Details', {
            'fields': ('wallet', 'amount', 'transaction_type', 'status')
        }),
        ('Reference Information', {
            'fields': ('reference_id', 'description')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    ordering = ['-created_at']
    
    def user_email(self, obj):
        return obj.wallet.user.email
    user_email.short_description = 'User'
    
    def transaction_type_badge(self, obj):
        colors = {
            'credit': 'green',
            'debit': 'red',
            'refund': 'blue'
        }
        color = colors.get(obj.transaction_type, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_transaction_type_display()
        )
    transaction_type_badge.short_description = 'Type'
    
    def amount_display(self, obj):
        color = 'green' if obj.transaction_type == 'credit' else 'red'
        symbol = '+' if obj.transaction_type == 'credit' else '-'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}₹{:,.2f}</span>',
            color,
            symbol,
            obj.amount
        )
    amount_display.short_description = 'Amount'
    
    def status_badge(self, obj):
        colors = {
            'pending': 'orange',
            'completed': 'green',
            'failed': 'red',
            'cancelled': 'gray'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def transaction_date(self, obj):
        return obj.created_at.strftime('%Y-%m-%d %H:%M:%S')
    transaction_date.short_description = 'Date & Time'

