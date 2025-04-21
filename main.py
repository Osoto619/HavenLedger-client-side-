import PySimpleGUI as sg
import api_functions as api

# Fetch data from API
facility_info = api.fetch_facility_info()  # Fetch facility names + beds
room_details = api.fetch_room_details()
room_occupancy = api.fetch_room_occupancy()
#print(room_occupancy) # Debugging line to check room occupancy data


def generate_room_buttons(facility_name):
    """Generate buttons based on room details fetched from API."""
    room_data = []
    if facility_name in room_details:
        for room in room_details[facility_name]:
            room_number = room["room"]
            status = room["status"]
            room_type = room["room_type"]  # Now determined dynamically

            # Determine color based on status
            if status == "Vacant":
                color = "red"
            elif room_type == "Semi-Private":
                color = "yellow"
            else:  # Private
                color = "green"

            room_label = f"Room {room_number}\n{room_type}"
            room_data.append((room_label, color))

    return room_data


# Function to add a new facility
def add_facility():
    layout = [
        [sg.Text("Add Facility", font=("Arial", 16, "bold"), justification="center", expand_x=True)],
        [sg.Text("Facility Name:"), sg.InputText(key="-FACILITY-NAME-", size=(30, 1))],
        [sg.Text("Total Beds:"), sg.InputText(key="-TOTAL-BEDS-", size=(30, 1))],
        [sg.Button("Add Facility", size=(20, 1)), sg.Button("Cancel", size=(20, 1))]
    ]
    
    window = sg.Window("Add Facility", layout, finalize=True)

    while True:
        event, values = window.read()
        if event in (sg.WINDOW_CLOSED, "Cancel"):
            break
        elif event == "Add Facility":
            facility_name = values["-FACILITY-NAME-"]
            total_beds = values["-TOTAL-BEDS-"]

            if not facility_name or not total_beds.isdigit():
                sg.popup("Please enter a valid facility name and number of beds.", title="Error")
                continue
            
            # Send data to API
            response = api.send_add_facility(facility_name, int(total_beds))

            if "error" in response:
                sg.popup(f"Error: {response['error']}", title="Error")
            else:
                sg.popup("Facility added successfully!", title="Success")
                window.close()
                # Refresh data after adding facility
                global room_details, room_occupancy
                room_details = api.fetch_room_details()
                room_occupancy = api.fetch_room_occupancy()

                break
    
    window.close()


# Function to add a new room to a facility
def add_room(facility_name):
    """GUI for adding a new room to a facility"""
    layout = [
        [sg.Text(f"Add Room to {facility_name}", font=("Arial", 16, "bold"), justification="center", expand_x=True)],
        [sg.Text("Room Number:"), sg.InputText(key="-ROOM-NUMBER-", size=(10, 1))],
        [sg.Button("Add Room", size=(15, 1)), sg.Button("Cancel", size=(15, 1))]
    ]

    window = sg.Window(f"Add Room - {facility_name}", layout, finalize=True)

    while True:
        event, values = window.read()
        if event in (sg.WINDOW_CLOSED, "Cancel"):
            break
        elif event == "Add Room":
            room_number = values["-ROOM-NUMBER-"]

            if not room_number:
                sg.popup("Please enter a room number.", title="Error")
                continue

            # Send request to API
            result = api.add_room_to_facility(facility_name, room_number)

            if "success" in result:
                sg.popup("Room added successfully!", title="Success")
                window.close()

                # ✅ Immediately refresh room details after adding a room
                global room_details
                room_details = api.fetch_room_details()

                # ✅ Refresh facility details UI to reflect the change
                show_facility_details(facility_name)
                break
            else:
                sg.popup(f"Error: {result.get('error', 'Unknown error')}", title="Error")

    window.close()


# Function to add or edit room resident(s)
def add_resident(facility_name, room_number):
    """GUI for adding a resident to a room."""
    layout = [
        [sg.Text(f"Add Resident to Room {room_number}", font=("Arial", 16, "bold"), justification="center", expand_x=True)],
        [sg.Text("Resident Name:"), sg.InputText(key="-RESIDENT-NAME-", size=(30, 1))],
        [sg.Text("Monthly Payment:"), sg.InputText(key="-MONTHLY-PAYMENT-", size=(30, 1))],
        [sg.Text("Payment Due Date (Day of Month):"), sg.InputText(key="-PAYMENT-DUE-DATE-", size=(10, 1))],
        [sg.Text("Move-In Date (YYYY-MM-DD):"), sg.InputText(key="-MOVE-IN-DATE-", size=(15, 1))],
        [sg.Button("Add Resident", size=(20, 1)), sg.Button("Cancel", size=(20, 1))]
    ]
    
    window = sg.Window(f"Add Resident - {facility_name}", layout, finalize=True)
    
    while True:
        event, values = window.read()
        if event in (sg.WINDOW_CLOSED, "Cancel"):
            break
        elif event == "Add Resident":
            resident_name = values["-RESIDENT-NAME-"]
            monthly_payment = values["-MONTHLY-PAYMENT-"].replace(",", "")  # Remove commas
            payment_due_date = values["-PAYMENT-DUE-DATE-"]
            move_in_date = values["-MOVE-IN-DATE-"]

            if not resident_name or not monthly_payment or not payment_due_date or not move_in_date:
                sg.popup("Please fill in all fields.", title="Error")
                continue

            try:
                monthly_payment = float(monthly_payment)  # Convert to a valid number
            except ValueError:
                sg.popup("Invalid payment amount. Please enter a valid number.", title="Error")
                continue

            # Call API function to add resident
            result = api.add_resident_to_room(facility_name, room_number, resident_name, monthly_payment, payment_due_date, move_in_date)

            if "success" in result:
                sg.popup("Resident added successfully!", title="Success")
                window.close()

                # ✅ Immediately refresh data after adding a resident
                global room_occupancy
                room_occupancy = api.fetch_room_occupancy()

                # ✅ Refresh room details UI to reflect the change
                show_room_details(facility_name, room_number)
                break
            else:
                sg.popup(f"Error: {result.get('error', 'Unknown error')}", title="Error")
    window.close()


def record_payment_window(facility_name, room_number, resident_name, expected_due_day):
    from datetime import date

    today = date.today()
    default_due_date = date(today.year, today.month, min(expected_due_day, 28))  # Avoid invalid dates

    layout = [
        [sg.Text(f"Record Payment for {resident_name}", font=("Arial", 16, "bold"), justification="center", expand_x=True)],
        [sg.Text("Payment Due Date (applies to):"), sg.Input(default_due_date.isoformat(), key="-DUE-DATE-", size=(15, 1)), sg.CalendarButton("📅", target="-DUE-DATE-", format="%Y-%m-%d")],
        [sg.Text("Payment Date (actual paid):"), sg.Input(today.isoformat(), key="-PAYMENT-DATE-", size=(15, 1)), sg.CalendarButton("📅", target="-PAYMENT-DATE-", format="%Y-%m-%d")],
        [sg.Text("Payment Method:"), sg.Combo(["Cash", "Check", "Debit/Credit"], key="-METHOD-", readonly=True, size=(20, 1))],
        [sg.Text("Notes (optional):"), sg.InputText(key="-NOTES-", size=(30, 1))],
        [sg.Button("Submit Payment", size=(20, 1)), sg.Button("Cancel", size=(15, 1))]
    ]

    window = sg.Window("Record Payment", layout, finalize=True)

    while True:
        event, values = window.read()
        if event in (sg.WINDOW_CLOSED, "Cancel"):
            break
        elif event == "Submit Payment":
            due_date = values["-DUE-DATE-"]
            payment_date = values["-PAYMENT-DATE-"]
            method = values["-METHOD-"]
            notes = values["-NOTES-"]

            if not due_date or not payment_date or not method:
                sg.popup("Please fill out all required fields (Due Date, Payment Date, Method).", title="Missing Info")
                continue

            window.close()
            return {
                "facility_name": facility_name,
                "room_number": room_number,
                "resident_name": resident_name,
                "payment_due_date": due_date,
                "payment_date": payment_date,
                "method": method,
                "notes": notes
            }

    window.close()
    return None  # In case user cancels


def show_room_details(facility_name, room_number):
    # Fetch resident details from room_occupancy
    residents = [
        [r["resident"], f"${r['amount']:,}", r["date"], r["status"]]
        for r in room_occupancy.get(facility_name, []) if r["room"] == room_number
    ]

    # Handle case where the room has no residents (Vacant)
    if not residents:
        residents = [["No Residents", "-", "-", "-"]]

    layout = [
        [sg.Text(f"Room {room_number} Details", font=("Arial", 16, "bold"), justification="center", expand_x=True)],
        [sg.Text("Resident(s)", font=("Arial", 14, "bold"))],
        [sg.Table(
            values=residents,
            headings=["Resident Name", "Monthly Payment", "Payment Due Date", "Status"],
            auto_size_columns=False,
            justification='center',
            col_widths=[20, 15, 15, 10],
            key="-RESIDENT-TABLE-",
            num_rows=min(len(residents), 5),  # Adjust based on number of residents
            enable_events=True,
        )],
        [
            sg.Button("Add Resident", size=(18, 1)),
            sg.Button("Edit Resident", size=(18, 1)),
            sg.Button("Remove Resident", size=(18, 1)),
            sg.Button("Mark as Paid", size=(18, 1)),  # Updated for real data
            sg.Button("Back", size=(18, 1))
        ]
    ]

    window = sg.Window(f"Room {room_number} Details", layout, finalize=True)

    while True:
        event, values = window.read()

        if event in (sg.WINDOW_CLOSED, "Back"):
            window.close()
            break

        elif event == "Add Resident":
            window.close()
            add_resident(facility_name, room_number)
            show_room_details(facility_name, room_number)  # Refresh the view
            break

        elif event == "Mark as Paid":
            selected = values["-RESIDENT-TABLE-"]
            if not selected or residents[selected[0]][0] == "No Residents":
                sg.popup("Please select a valid resident.", title="No selection")
            else:
                row_index = selected[0]
                resident_name = residents[row_index][0]

                # Find the expected due day for that resident
                expected_due_day = int(residents[row_index][2]) if residents[row_index][2].isdigit() else 1

                # Open payment input window
                payment_info = record_payment_window(facility_name, room_number, resident_name, expected_due_day)
                print(payment_info)  # Debugging line to check payment info

                if payment_info:
                    result = api.record_payment(payment_info)

                    # sg.popup(f"Payment recorded for {resident_name}.", title="Success")
                    if "success" in result:
                        sg.popup(f"Payment recorded for {resident_name}.", title="Success")

                        # # Refresh room occupancy
                        # global room_occupancy
                        # room_occupancy = api.fetch_room_occupancy()

                        window.close()
                        show_room_details(facility_name, room_number)
                        break
                    else:
                        sg.popup(f"Error: {result.get('error', 'Unknown error')}", title="Error")

                    # # Refresh room occupancy
                    # global room_occupancy
                    # room_occupancy = api.fetch_room_occupancy()

                    window.close()
                    show_room_details(facility_name, room_number)
                    break
        
        elif event == "Remove Resident":
            selected = values["-RESIDENT-TABLE-"]
            if not selected or residents[selected[0]][0] == "No Residents":
                sg.popup("Please select a valid resident to remove.", title="No selection")
            else:
                row_index = selected[0]
                resident_name = residents[row_index][0]

                confirm = sg.popup_yes_no(f"Are you sure you want to remove {resident_name}?", title="Confirm Removal")
                if confirm == "Yes":
                    result = api.remove_resident_from_room(facility_name, room_number, resident_name)

                    if "success" in result:
                        sg.popup(f"{resident_name} removed successfully.", title="Success")
                        
                        # Refresh room occupancy and view
                        # global room_occupancy
                        # room_occupancy = api.fetch_room_occupancy()

                        window.close()
                        show_room_details(facility_name, room_number)  # Reload updated UI
                        break
                    else:
                        sg.popup(f"Error: {result.get('error', 'Unknown error')}", title="Error")

    window.close()


def show_facility_details(facility_name):
    """Displays the facility details window, including rooms and residents"""
    room_data = generate_room_buttons(facility_name)  # ✅ Fetch updated rooms
    payment_data = room_occupancy.get(facility_name, [])
    payment_table_data = [[p["room"], p["resident"], p["amount"], p["status"], p["date"]] for p in payment_data]

    layout = [
        [sg.Text(f"{facility_name} - Room Overview", font=("Arial", 16, "bold"))],
        [sg.Column([
            [sg.Button(name, key=f"ROOM-{name}", size=(12, 3), button_color=("black", color), font=("Arial", 10, "bold")) 
             for name, color in room_data[i:i+5]]
            for i in range(0, len(room_data), 5)
        ])],
        [
            sg.Text("Legend:"),
            sg.Text("Red = Vacant"),
            sg.Text("Yellow = Occupied (Semi-Private)"),
            sg.Text("Green = Occupied (Private)")
        ],
        [sg.Text("Resident Payments", font=("Arial", 14, "bold"))],
        [sg.Table(
            values=payment_table_data,
            headings=["Room #", "Resident Name", "Amount Due", "Payment Status", "Payment Date"],
            auto_size_columns=False,
            justification='center',
            col_widths=[10, 20, 15, 15, 10],
            key="-PAYMENT-TABLE-",
            num_rows=min(len(payment_table_data), 10),
        )],
        [sg.Button("Add Room", key="ADD_ROOM"), sg.Button("Back", key="BACK")]
    ]

    window = sg.Window(f"{facility_name} - Details", layout, finalize=True)
    while True:
        event, values = window.read()
        if event in (sg.WINDOW_CLOSED, "BACK"):
            window.close()
            break
        elif event == "ADD_ROOM":
            window.close()
            add_room(facility_name)
            show_facility_details(facility_name)  # ✅ Reload facility details to show new room
            break
        elif event.startswith("ROOM-"):
            room_number = [int(s) for s in event.split() if s.isdigit()][0]
            window.close()
            show_room_details(facility_name, room_number)
            show_facility_details(facility_name)  # ✅ Reload after viewing room details
            break
    window.close()

# # Function to show the facility overview
# def show_facility_overview():
#     # Dynamically compute facility summary
#     facility_summary = {}

#     for facility, rooms in room_details.items():
#         total_vacant = sum(1 for r in rooms if r["status"] == "Vacant")
#         total_partial = sum(1 for r in rooms if r["status"] == "Partially Occupied")
#         total_occupied = sum(1 for r in rooms if r["status"] == "Occupied")
        
#         # Calculate total revenue by summing all resident payments in that facility
#         total_revenue = sum(r["amount"] for r in room_occupancy.get(facility, []))

#         # Count overdue and upcoming payments
#         overdue_count = sum(1 for r in room_occupancy.get(facility, []) if r["status"] == "Overdue")
#         upcoming_due_count = sum(1 for r in room_occupancy.get(facility, []) if r["status"] == "Upcoming Due")

#         facility_summary[facility] = {
#             "vacant": total_vacant,
#             "partial": total_partial,
#             "occupied": total_occupied,
#             "monthly_revenue": total_revenue,
#             "overdue": overdue_count,
#             "upcoming_due": upcoming_due_count
#         }
#     layout = [
#         [sg.Text("HavenLedger - Facility Overview", font=("Arial", 16, "bold"))],
#         [sg.Text(f"Total Monthly Revenue Across Facilities: ${sum(f['monthly_revenue'] for f in facility_summary.values()):,}", font=("Arial", 14, "bold"))],
#         [sg.Table(
#             values=[
#                 [
#                     fac, 
#                     facility_summary.get(fac, {}).get("vacant", 0),
#                     f"${facility_summary.get(fac, {}).get('monthly_revenue', 0):,}",
#                     facility_summary.get(fac, {}).get("overdue", 0),
#                     facility_summary.get(fac, {}).get("upcoming_due", 0),
#                     facility_info.get(fac, {}).get("total_beds", "N/A")  # Ensure facility exists in `facility_info`
#                 ] 
#                 for fac in facility_info.keys()  # Show all facilities, even if no rooms
#             ],
#             headings=["Facility Name", "Vacant", "Monthly Revenue", "Overdue", "Upcoming Due", "Total Beds"],
#             auto_size_columns=False,
#             justification='center',
#             col_widths=[20, 10, 15, 10, 10, 10],
#             key="-FACILITY-TABLE-",
#             enable_events=True,
#             num_rows=10
#         )],
#         [sg.Button("View Facility Details", size=(20, 1)), sg.Button("Add Facility", size=(15, 1)), sg.Button("Exit", size=(15, 1))]
#     ]
    
#     window = sg.Window("HavenLedger - Facility Overview", layout, finalize=True)
#     while True:
#         event, values = window.read()
#         if event in (sg.WINDOW_CLOSED, "Exit"):
#             window.close()
#             break
#         elif event == "View Facility Details":
#             selected_rows = values["-FACILITY-TABLE-"]
#             if selected_rows:
#                 selected_facility = list(facility_info.keys())[selected_rows[0]]
#                 window.close()
#                 show_facility_details(selected_facility)
#                 show_facility_overview()
#         elif event == "Add Facility":
#             window.close()
#             add_facility()
#             show_facility_overview()
#             break
#     window.close()
def show_facility_overview():
    # Dynamically compute facility summary
    facility_summary = {}

    for facility, rooms in room_details.items():
        total_vacant = sum(1 for r in rooms if r["status"] == "Vacant")
        total_partial = sum(1 for r in rooms if r["status"] == "Partially Occupied")
        total_occupied = sum(1 for r in rooms if r["status"] == "Occupied")
        
        # Calculate total revenue by summing all resident payments in that facility
        total_revenue = sum(r["amount"] for r in room_occupancy.get(facility, []))

        # Count overdue and upcoming payments
        overdue_count = sum(1 for r in room_occupancy.get(facility, []) if r["status"] == "Overdue")
        upcoming_due_count = sum(1 for r in room_occupancy.get(facility, []) if r["status"] == "Upcoming Due")

        facility_summary[facility] = {
            "vacant": total_vacant,
            "partial": total_partial,
            "occupied": total_occupied,
            "monthly_revenue": total_revenue,
            "overdue": overdue_count,
            "upcoming_due": upcoming_due_count
        }
    
    layout = [
        [sg.Text("HavenLedger - Facility Overview", font=("Arial", 16, "bold"))],
        [sg.Text(f"Total Monthly Revenue Across Facilities: ${sum(f['monthly_revenue'] for f in facility_summary.values()):,}", font=("Arial", 14, "bold"))],
        [sg.Text("Resident Locator:"), sg.InputText(key="-RESIDENT-SEARCH-", size=(30, 1)), sg.Button("Search")],
        [sg.Table(
            values=[
                [
                    fac, 
                    facility_summary.get(fac, {}).get("vacant", 0),
                    f"${facility_summary.get(fac, {}).get('monthly_revenue', 0):,}",
                    facility_summary.get(fac, {}).get("overdue", 0),
                    facility_summary.get(fac, {}).get("upcoming_due", 0),
                    facility_info.get(fac, {}).get("total_beds", "N/A")  # Ensure facility exists in `facility_info`
                ] 
                for fac in facility_info.keys()  # Show all facilities, even if no rooms
            ],
            headings=["Facility Name", "Vacant", "Monthly Revenue", "Overdue", "Upcoming Due", "Total Beds"],
            auto_size_columns=False,
            justification='center',
            col_widths=[20, 10, 15, 10, 10, 10],
            key="-FACILITY-TABLE-",
            enable_events=True,
            num_rows=10
        )],
        [sg.Button("View Facility Details", size=(20, 1)), sg.Button("Add Facility", size=(15, 1)), sg.Button("Exit", size=(15, 1))]
    ]
    
    window = sg.Window("HavenLedger - Facility Overview", layout, finalize=True)
    while True:
        event, values = window.read()
        if event in (sg.WINDOW_CLOSED, "Exit"):
            window.close()
            break
        elif event == "Search":
            resident_name = values["-RESIDENT-SEARCH-"].strip()
            found = None
            for facility, residents in room_occupancy.items():
                for res in residents:
                    if res["resident"].lower() == resident_name.lower():
                        found = (facility, res["room"])
                        break
                if found:
                    break
            if found:
                sg.popup(f"{resident_name} is in {found[0]}, Room {found[1]}", title="Resident Found")
            else:
                sg.popup(f"{resident_name} not found in the system.", title="Resident Not Found")
        elif event == "View Facility Details":
            selected_rows = values["-FACILITY-TABLE-"]
            if selected_rows:
                selected_facility = list(facility_info.keys())[selected_rows[0]]
                window.close()
                show_facility_details(selected_facility)
                show_facility_overview()
        elif event == "Add Facility":
            window.close()
            add_facility()
            show_facility_overview()
            break
    window.close()

# Start the program with the overview
show_facility_overview()
