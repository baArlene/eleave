import streamlit as st
import pandas as pd
from datetime import date, datetime
import os
import plotly.express as px
from io import BytesIO

# --------------- CONFIG & SETUP ----------------
st.set_page_config(
    page_title="E-Leave Management System",
    page_icon="📅",
    layout="wide"
)

# --- Custom CSS for Theming and Buttons ---
st.markdown("""
    <style>
        .centered-title {
            text-align: center;
            color: #3498DB;
        }
        .leave-card {
            border: 1px solid #282F3B;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 15px;
            background-color: #282F3B;
        }
        div.stButton > button:first-child {
            background-color: #3498DB;
            color: white;
            border: none;
            border-radius: 8px;
            height: 40px;
            margin-top: 5px;
            font-weight: bold;
        }
        div.stButton > button:first-child:hover {
            background-color: #2980B9;
        }
        div[data-testid="stExpander"] button {
            background-color: #E74C3C !important;
        }
        div[data-testid="stExpander"] button:hover {
            background-color: #C0392B !important;
        }
    </style>
""", unsafe_allow_html=True)

# --- File Paths ---
REQUEST_FILE = "leave_requests.csv"
AUDIT_FILE = "audit_trail.csv"
USERS_FILE = "users.csv"
BALANCE_FILE = "leave_balance.csv"
UPLOADS_DIR = "uploads"

# --- Initialize CSV Files ---
def init_csv_files():
    if not os.path.exists(REQUEST_FILE):
        pd.DataFrame(columns=["Employee", "Department", "LeaveType", "StartDate", "EndDate", "Status", "Reason", "Document"]).to_csv(REQUEST_FILE, index=False)
    
    if not os.path.exists(AUDIT_FILE):
        pd.DataFrame(columns=["Timestamp", "Action", "Employee", "Details", "ManagerComments"]).to_csv(AUDIT_FILE, index=False)
        
    if not os.path.exists(UPLOADS_DIR):
        os.makedirs(UPLOADS_DIR)
        
    if not os.path.exists(USERS_FILE):
        default_users = {
            "Employee": ["John Doe", "Jane Smith", "Peter Jones", "Mary Brown", "David Williams", "Susan Davis"],
            "Department": ["Finance", "HR", "Finance", "HR", "IT", "IT"],
            "Role": ["manager", "manager", "employee", "employee", "manager", "employee"]
        }
        pd.DataFrame(default_users).to_csv(USERS_FILE, index=False)

    if not os.path.exists(BALANCE_FILE):
        default_balances = {
            "Employee": ["John Doe", "Jane Smith", "Peter Jones", "Mary Brown", "David Williams", "Susan Davis"],
            "Annual": [20, 20, 20, 20, 20, 20],
            "Sick": [10, 10, 10, 10, 10, 10]
        }
        pd.DataFrame(default_balances).to_csv(BALANCE_FILE, index=False)

def safe_read_csv(file_path):
    try:
        return pd.read_csv(file_path)
    except Exception as e:
        st.error(f"Error reading {file_path}: {e}")
        return pd.DataFrame()

# Initialize
init_csv_files()

if "leave_requests" not in st.session_state:
    st.session_state.leave_requests = safe_read_csv(REQUEST_FILE)
    # Add this for robust conversion
    st.session_state.leave_requests['StartDate'] = pd.to_datetime(st.session_state.leave_requests['StartDate'], errors='coerce')
    st.session_state.leave_requests['EndDate'] = pd.to_datetime(st.session_state.leave_requests['EndDate'], errors='coerce')

    st.session_state.audit_trail = safe_read_csv(AUDIT_FILE)
    st.session_state.users = safe_read_csv(USERS_FILE)
    st.session_state.leave_balance = safe_read_csv(BALANCE_FILE)

# ---------------- HEADER ----------------
col1, col2 = st.columns([1, 4])
with col1:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=120)
with col2:
    st.markdown("<h1 class='centered-title'>E-Leave Management System Prototype</h1>", unsafe_allow_html=True)
st.markdown("---")

# ---------------- LOGIN ----------------
st.sidebar.header("User Login")
if not st.session_state.users.empty:
    all_employees = st.session_state.users["Employee"].tolist()
    selected_user = st.sidebar.selectbox("Select a User to log in:", options=all_employees)

    logged_in_user_data = st.session_state.users[st.session_state.users["Employee"] == selected_user].iloc[0]
    logged_in_name = logged_in_user_data["Employee"]
    logged_in_department = logged_in_user_data["Department"]
    logged_in_role = logged_in_user_data["Role"]
    
    st.sidebar.info(f"Logged in as **{logged_in_name}** ({logged_in_role}) from the **{logged_in_department}** department.")
else:
    st.error("User data not found. Please check your `users.csv` file.")

# ---------------- TABS ----------------
if logged_in_role == "employee":
    tab1, tab3 = st.tabs(["📝 Apply Leave", "📊 Dashboard"])
elif logged_in_role == "manager":
    tab2, tab3 = st.tabs(["✅ Manager Approval", "📊 Dashboard"])
else:
    st.warning("Please select a valid user to continue.")
    tab1, tab2, tab3 = st.tabs(["", "", ""])

# ---------------- EMPLOYEE TAB ----------------
if logged_in_role == "employee":
    with tab1:
        st.header("Apply for Leave")

        with st.form("leave_form", clear_on_submit=True):
            st.write(f"Applying for leave as **{logged_in_name}** from **{logged_in_department}** department.")
            
            leave_type = st.selectbox("Leave Type", ["Annual", "Sick", "Maternity", "Paternity", "Study"])
            start_date = st.date_input("Start Date", value=date.today())
            end_date = st.date_input("End Date", value=date.today())
            reason = st.text_area("Reason for Leave")
            file_upload = st.file_uploader("Upload Supporting Document", type=["pdf", "png", "jpg", "jpeg"])
            
            submitted = st.form_submit_button("Submit Leave")

            if submitted:
                if end_date < start_date:
                    st.warning("End Date cannot be before the Start Date.")
                else:
                    doc_path = ""
                    if file_upload:
                        doc_path = os.path.join(UPLOADS_DIR, f"{logged_in_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file_upload.name}")
                        with open(doc_path, "wb") as f:
                            f.write(file_upload.getbuffer())

                    new_row = {
                        "Employee": logged_in_name,
                        "Department": logged_in_department,
                        "LeaveType": leave_type,
                        "StartDate": start_date,
                        "EndDate": end_date,
                        "Status": "Pending",
                        "Reason": reason,
                        "Document": doc_path
                    }
                    
                    st.session_state.leave_requests = pd.concat([st.session_state.leave_requests, pd.DataFrame([new_row])], ignore_index=True)
                    st.session_state.leave_requests.to_csv(REQUEST_FILE, index=False)

                    audit_log = {
                        "Timestamp": datetime.now(),
                        "Action": "Submit Leave",
                        "Employee": logged_in_name,
                        "Details": f"{leave_type} leave submitted ({start_date} to {end_date})",
                        "ManagerComments": ""
                    }
                    st.session_state.audit_trail = pd.concat([st.session_state.audit_trail, pd.DataFrame([audit_log])], ignore_index=True)
                    st.session_state.audit_trail.to_csv(AUDIT_FILE, index=False)

                    st.success("Leave submitted successfully!")
                    st.info(f"📧 Simulated Email: Manager of {logged_in_department} notified of new leave request from {logged_in_name}")

        st.markdown("---")
        st.subheader("Your Leave Request History")
        employee_requests = st.session_state.leave_requests[st.session_state.leave_requests["Employee"] == logged_in_name]
        if employee_requests.empty:
            st.info(f"You have not submitted any leave requests yet.")
        else:
            st.data_editor(
                employee_requests.sort_values("StartDate", ascending=False),
                use_container_width=True,
                hide_index=True
            )

# ---------------- MANAGER TAB ----------------
if logged_in_role == "manager":
    with tab2:
        st.header("Pending Leave Approvals")
        st.write(f"Showing pending requests for the **{logged_in_department}** department.")
        
        pending_requests = st.session_state.leave_requests[
            (st.session_state.leave_requests["Status"] == "Pending") & 
            (st.session_state.leave_requests["Department"] == logged_in_department)
        ]

        if pending_requests.empty:
            st.info("No pending leave requests available.")
        else:
            for idx, row in pending_requests.iterrows():
                with st.container(border=True):
                    st.markdown(f"**Employee:** {row['Employee']}")
                    st.markdown(f"**Leave Type:** {row['LeaveType']}")
                    st.markdown(f"**Period:** {row['StartDate'].strftime('%Y-%m-%d')} → {row['EndDate'].strftime('%Y-%m-%d')}")
                    st.markdown(f"**Reason:** {row['Reason']}")
                    
                    if row['Document']:
                        st.write("---")
                        st.markdown("Attached Document:")
                        file_extension = os.path.splitext(row['Document'])[1].lower()
                        try:
                            if file_extension in [".png", ".jpg", ".jpeg"]:
                                st.image(row['Document'], caption="Supporting Document")
                            elif file_extension == ".pdf":
                                with open(row['Document'], "rb") as pdf_file:
                                    st.download_button(
                                        label="Download PDF Document",
                                        data=pdf_file,
                                        file_name=os.path.basename(row['Document']),
                                        mime="application/pdf"
                                    )
                        except FileNotFoundError:
                            st.error("Document not found.")

                    col1, col2 = st.columns(2)
                    
                    if col1.button("Approve", key=f"approve_{idx}", use_container_width=True):
                        st.session_state.leave_requests.loc[idx, "Status"] = "Approved"
                        st.session_state.leave_requests.to_csv(REQUEST_FILE, index=False)

                        # Deduct leave balance
                        days_taken = (pd.to_datetime(row['EndDate']) - pd.to_datetime(row['StartDate'])).days + 1
                        balance_idx = st.session_state.leave_balance[st.session_state.leave_balance["Employee"] == row['Employee']].index
                        if not balance_idx.empty and row['LeaveType'] in ["Annual", "Sick"]:
                            col_name = row['LeaveType']
                            current_balance = st.session_state.leave_balance.loc[balance_idx[0], col_name]
                            st.session_state.leave_balance.loc[balance_idx[0], col_name] = max(current_balance - days_taken, 0)
                            st.session_state.leave_balance.to_csv(BALANCE_FILE, index=False)

                        audit_log = {
                            "Timestamp": datetime.now(),
                            "Action": "Approve Leave",
                            "Employee": row['Employee'],
                            "Details": f"Manager approved {row['LeaveType']} leave",
                            "ManagerComments": ""
                        }
                        st.session_state.audit_trail = pd.concat([st.session_state.audit_trail, pd.DataFrame([audit_log])], ignore_index=True)
                        st.session_state.audit_trail.to_csv(AUDIT_FILE, index=False)

                        st.success(f"Leave approved for {row['Employee']}! Remaining {row['LeaveType']} days updated.")
                        st.experimental_rerun()
                    
                    with col2:
                        with st.expander("Reject"):
                            rejection_reason = st.text_area("Reason for rejection:", key=f"reason_{idx}")
                            if st.button("Submit Rejection", key=f"reject_btn_{idx}", use_container_width=True):
                                if not rejection_reason.strip():
                                    st.warning("Please provide a reason for rejection.")
                                else:
                                    st.session_state.leave_requests.loc[idx, "Status"] = "Rejected"
                                    st.session_state.leave_requests.loc[idx, "Reason"] = rejection_reason
                                    st.session_state.leave_requests.to_csv(REQUEST_FILE, index=False)
                                    audit_log = {
                                        "Timestamp": datetime.now(),
                                        "Action": "Reject Leave",
                                        "Employee": row['Employee'],
                                        "Details": f"Manager rejected {row['LeaveType']} leave",
                                        "ManagerComments": rejection_reason
                                    }
                                    st.session_state.audit_trail = pd.concat([st.session_state.audit_trail, pd.DataFrame([audit_log])], ignore_index=True)
                                    st.session_state.audit_trail.to_csv(AUDIT_FILE, index=False)
                                    st.error(f"Leave rejected for {row['Employee']}.")
                                    st.experimental_rerun()

# ---------------- DASHBOARD TAB ----------------
with tab3:
    # st.header("Leave Dashboard")

    if logged_in_role == "employee":
        st.header(f"{logged_in_name}")
        
        # Leave balances
        user_balance = st.session_state.leave_balance[st.session_state.leave_balance["Employee"] == logged_in_name]
        if not user_balance.empty:
            col1, col2 = st.columns(2)
            col1.metric("Annual Leave Remaining", f"{user_balance['Annual'].iloc[0]} days")
            col2.metric("Sick Leave Remaining", f"{user_balance['Sick'].iloc[0]} days")

        st.markdown("---")
        
        # Personal leave requests
        employee_requests = st.session_state.leave_requests[st.session_state.leave_requests["Employee"] == logged_in_name]
        if not employee_requests.empty:
            status_counts = employee_requests["Status"].value_counts().reset_index()
            status_counts.columns = ["Status", "Count"]

            fig = px.pie(status_counts, names="Status", values="Count", title="Your Leave Status Overview", hole=0.4)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("You have no leave requests to display on the dashboard.")
            
    elif logged_in_role == "manager":
        st.subheader(f"{logged_in_department} Department")
        
        dept_requests = st.session_state.leave_requests[st.session_state.leave_requests["Department"] == logged_in_department]
        if not dept_requests.empty:
            pending_count = dept_requests[dept_requests["Status"] == "Pending"].shape[0]
            approved_count = dept_requests[dept_requests["Status"] == "Approved"].shape[0]
            rejected_count = dept_requests[dept_requests["Status"] == "Rejected"].shape[0]
        
            col1, col2, col3 = st.columns(3)
            col1.metric("Pending Team Requests", pending_count)
            col2.metric("Approved Team Requests", approved_count)
            col3.metric("Rejected Team Requests", rejected_count)

            st.markdown("---")
            st.subheader("Team Leave Status Distribution")
            fig2 = px.pie(dept_requests, names="Status", title=f"Leave Status Overview for {logged_in_department}", hole=0.4)
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info(f"No leave requests to display for the {logged_in_department} department.")
        
    st.markdown("---")

    # --- Audit Trail for Managers ---
    if logged_in_role == "manager":
        st.subheader("Audit Trail (Recent Actions)")
        
        # Filter the audit trail to show only actions for the manager's department
        dept_employees = st.session_state.users[st.session_state.users["Department"] == logged_in_department]["Employee"].tolist()
        
        # Use a copy to avoid SettingWithCopyWarning
        filtered_audit = st.session_state.audit_trail[st.session_state.audit_trail["Employee"].isin(dept_employees)].copy()

        if not filtered_audit.empty:
            filtered_audit["Timestamp"] = pd.to_datetime(filtered_audit["Timestamp"], errors="coerce")
            filtered_audit = filtered_audit.sort_values(by="Timestamp", ascending=False)
            filtered_audit["Timestamp"] = filtered_audit["Timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")

            # Filters
            col1, col2 = st.columns(2)
            emp_filter = col1.text_input("Filter by Employee:")
            action_filter = col2.text_input("Filter by Action:")

            if emp_filter:
                filtered_audit = filtered_audit[filtered_audit["Employee"].str.contains(emp_filter, case=False, na=False)]
            if action_filter:
                filtered_audit = filtered_audit[filtered_audit["Action"].str.contains(action_filter, case=False, na=False)]

            st.data_editor(
                filtered_audit[["Timestamp", "Action", "Employee", "Details", "ManagerComments"]].head(20),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No audit logs available for your department.")
    
    st.markdown("---")

    st.subheader("Export Leave Data")
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        st.session_state.leave_requests.to_excel(writer, index=False, sheet_name='LeaveRequests')
        st.session_state.audit_trail.to_excel(writer, index=False, sheet_name='AuditTrail')
        st.session_state.leave_balance.to_excel(writer, index=False, sheet_name='LeaveBalance')
    st.download_button(
        label="📥 Download Excel Report",
        data=buffer,
        file_name="E-Leave_Report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )