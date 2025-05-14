from fastapi import APIRouter, Depends, Response, HTTPException
from sqlalchemy.orm import Session
from io import StringIO, BytesIO
import csv
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from datetime import datetime

from .database import get_db
from .models import LeaveRequest, User
from .auth import get_current_user

router = APIRouter()


# --------------------- CSV Export ---------------------
@router.get("/reports/leaves/csv")
def export_leaves_csv(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Export leave records as CSV (L5 Admin only)."""
    if current_user.role != "l5":
        raise HTTPException(status_code=403, detail="Only L5 Admins can access this")

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Associate", "Leave Type", "Start Date", "End Date", "Status"])

    # JOIN instead of repeated .get()
    leaves = db.query(LeaveRequest).join(User, LeaveRequest.user_id == User.id).all()
    for leave in leaves:
        writer.writerow([leave.user.username, leave.leave_type, leave.start_date, leave.end_date, leave.status])

    output.seek(0)
    filename = f"leave_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(
        content=output.read(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# --------------------- PDF Export ---------------------
@router.get("/reports/leaves/pdf")
def export_leaves_pdf(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Export leave records as PDF (L5 Admin only)."""
    if current_user.role != "l5":
        raise HTTPException(status_code=403, detail="Only L5 Admins can access this")

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(30, height - 40, "Leave Report")
    pdf.setFont("Helvetica", 10)

    y = height - 60
    pdf.drawString(30, y, "Name | Leave Type | Start | End | Status")
    y -= 20

    # JOIN instead of repeated .get()
    leaves = db.query(LeaveRequest).join(User, LeaveRequest.user_id == User.id).all()
    for leave in leaves:
        line = f"{leave.user.username} | {leave.leave_type} | {leave.start_date} | {leave.end_date} | {leave.status}"
        pdf.drawString(30, y, line)
        y -= 15
        if y < 50:
            pdf.showPage()
            pdf.setFont("Helvetica", 10)
            y = height - 40

    pdf.save()
    buffer.seek(0)
    filename = f"leave_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    return Response(
        content=buffer.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
