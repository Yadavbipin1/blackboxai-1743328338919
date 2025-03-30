import os
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import logging
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def calculate_bill(guest, room, last_bill_date, current_date, discount=0):
    """
    Calculate bill amount for a guest
    
    Args:
        guest: Guest model instance
        room: Room model instance
        last_bill_date: datetime object of last bill date
        current_date: datetime object of current date
        discount: float, discount amount
    
    Returns:
        tuple: (total_days, total_amount)
    """
    try:
        # Calculate total days
        delta = current_date - last_bill_date
        total_days = delta.days
        
        # Calculate daily rate (monthly rate / 30)
        daily_rate = room.price_per_month / 30
        
        # Calculate total amount
        total_amount = (total_days * daily_rate) - discount
        
        return total_days, round(total_amount, 2)
    
    except Exception as e:
        logger.error(f"Error calculating bill: {str(e)}")
        raise

def generate_bill_pdf(bill, guest, room):
    """
    Generate PDF bill for a guest
    
    Args:
        bill: Bill model instance
        guest: Guest model instance
        room: Room model instance
    
    Returns:
        str: Path to generated PDF file
    """
    try:
        # Create the bills directory for current month if it doesn't exist
        bills_folder = Config.get_current_bills_folder()
        
        # Generate PDF filename
        filename = f"bill_{guest.full_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(bills_folder, filename)
        
        # Create PDF document
        doc = SimpleDocTemplate(filepath, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []
        
        # Add title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30
        )
        elements.append(Paragraph("Hostel Bill", title_style))
        elements.append(Spacer(1, 12))
        
        # Add bill details
        bill_date = datetime.now().strftime("%d-%m-%Y")
        bill_info = [
            ["Bill Date:", bill_date],
            ["Guest Name:", guest.full_name],
            ["Room Number:", room.room_number],
            ["Room Type:", room.room_type],
            ["Period:", f"{bill.billing_month}-{bill.billing_year}"],
            ["Total Days:", str(bill.total_days)],
            ["Rate per Month:", f"₹{room.price_per_month}"],
            ["Discount:", f"₹{bill.discount}"],
            ["Total Amount:", f"₹{bill.total_amount}"]
        ]
        
        # Create table
        table = Table(bill_info, colWidths=[2*inch, 4*inch])
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(table)
        
        # Add footer
        elements.append(Spacer(1, 30))
        footer_text = "Thank you for staying with us!"
        elements.append(Paragraph(footer_text, styles["Normal"]))
        
        # Build PDF
        doc.build(elements)
        logger.info(f"PDF bill generated successfully: {filepath}")
        
        return filepath
    
    except Exception as e:
        logger.error(f"Error generating PDF bill: {str(e)}")
        raise

def generate_monthly_report_pdf(year, month, income_data, expense_data):
    """
    Generate monthly financial report PDF
    
    Args:
        year: int, year of report
        month: int, month of report
        income_data: list of income records
        expense_data: list of expense records
    
    Returns:
        str: Path to generated PDF file
    """
    try:
        # Create the reports directory if it doesn't exist
        reports_folder = os.path.join(Config.BASE_DIR, "reports")
        if not os.path.exists(reports_folder):
            os.makedirs(reports_folder)
        
        # Generate PDF filename
        filename = f"monthly_report_{year}_{month}.pdf"
        filepath = os.path.join(reports_folder, filename)
        
        # Create PDF document
        doc = SimpleDocTemplate(filepath, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []
        
        # Add title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30
        )
        elements.append(Paragraph(f"Financial Report - {month}/{year}", title_style))
        elements.append(Spacer(1, 12))
        
        # Calculate totals
        total_income = sum(record['amount'] for record in income_data)
        total_expenses = sum(record['amount'] for record in expense_data)
        net_balance = total_income - total_expenses
        
        # Add summary
        summary_data = [
            ["Total Income:", f"₹{total_income}"],
            ["Total Expenses:", f"₹{total_expenses}"],
            ["Net Balance:", f"₹{net_balance}"]
        ]
        
        summary_table = Table(summary_data, colWidths=[2*inch, 4*inch])
        summary_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(summary_table)
        elements.append(Spacer(1, 20))
        
        # Add detailed income table
        elements.append(Paragraph("Income Details", styles['Heading2']))
        elements.append(Spacer(1, 12))
        
        income_table_data = [["Date", "Guest", "Amount", "Status"]]
        for record in income_data:
            income_table_data.append([
                record['date'].strftime("%d-%m-%Y"),
                record['guest_name'],
                f"₹{record['amount']}",
                record['status']
            ])
        
        income_table = Table(income_table_data, colWidths=[1.5*inch, 2*inch, 1.5*inch, 1.5*inch])
        income_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey)
        ]))
        
        elements.append(income_table)
        elements.append(Spacer(1, 20))
        
        # Add detailed expense table
        elements.append(Paragraph("Expense Details", styles['Heading2']))
        elements.append(Spacer(1, 12))
        
        expense_table_data = [["Date", "Category", "Description", "Amount"]]
        for record in expense_data:
            expense_table_data.append([
                record['date'].strftime("%d-%m-%Y"),
                record['category'],
                record['description'],
                f"₹{record['amount']}"
            ])
        
        expense_table = Table(expense_table_data, colWidths=[1.5*inch, 1.5*inch, 2*inch, 1.5*inch])
        expense_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey)
        ]))
        
        elements.append(expense_table)
        
        # Build PDF
        doc.build(elements)
        logger.info(f"Monthly report PDF generated successfully: {filepath}")
        
        return filepath
    
    except Exception as e:
        logger.error(f"Error generating monthly report PDF: {str(e)}")
        raise

def auto_generate_bills():
    """
    Automatically generate bills for all active guests on the 27th of each month
    """
    from models import Guest, Room, Bill
    
    try:
        current_date = datetime.now()
        
        # Only proceed if it's the 27th of the month
        if current_date.day == 27:
            logger.info("Starting automatic bill generation")
            
            # Get all guests
            guests = Guest.query.all()
            
            for guest in guests:
                try:
                    # Get associated room
                    room = Room.query.filter_by(id=guest.room_id).first()
                    if not room:
                        logger.warning(f"No room found for guest {guest.id}")
                        continue
                    
                    # Calculate bill
                    last_bill_date = guest.last_bill_date or guest.check_in_date
                    total_days, total_amount = calculate_bill(
                        guest, room, last_bill_date, current_date
                    )
                    
                    # Create new bill
                    bill = Bill(
                        guest_id=guest.id,
                        room_id=room.id,
                        billing_month=current_date.month,
                        billing_year=current_date.year,
                        total_days=total_days,
                        total_amount=total_amount,
                        generated_date=current_date
                    )
                    
                    # Generate PDF
                    pdf_path = generate_bill_pdf(bill, guest, room)
                    bill.pdf_path = pdf_path
                    
                    # Update guest's last bill date
                    guest.last_bill_date = current_date
                    
                    # Save to database
                    db.session.add(bill)
                    db.session.commit()
                    
                    logger.info(f"Bill generated successfully for guest {guest.id}")
                
                except Exception as e:
                    logger.error(f"Error generating bill for guest {guest.id}: {str(e)}")
                    db.session.rollback()
                    continue
            
            logger.info("Automatic bill generation completed")
    
    except Exception as e:
        logger.error(f"Error in auto_generate_bills: {str(e)}")
        raise