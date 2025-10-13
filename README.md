# Hotel-Management-System

A complete hotel management system built with Flask and SQLite for efficient hotel operations.

## 🌟Features:

- **Reservation Management** - Create, view, edit, and cancel reservations

- **Room Management** - Track room availability and status

- **Guest Management** - Store guest information and contact details

- **Check-in/Check-out** - Streamlined guest processing

- **Dashboard** - Real-time hotel statistics and occupancy rates

## Installation:

### 1. Clone the repository:

    git clone https://github.com/maredishiva/hotel-management-system.git

    cd hotel-management-system

### 2. Install dependencies

    pip install flask

    pip install -r requirements.txt

### 3. Run the application

    python app.py

### 4. Access the system

- Open your browser and go to: http://localhost:5001

- The system automatically creates the database with sample data

## ⚙️ HOW TO USE:

### 1. View Dashboard

- Open http://localhost:5001
  
- See real-time hotel statistics
  
- Check occupancy rates and revenue

### 2. Manage Rooms

- Click "Rooms" in navigation
  
- View all rooms with status (Available/Occupied)

- Mark rooms as cleaned after checkout

- See room types, prices, and capacities

### 3. Create Reservations

- Click "New Reservation" button

- Select dates and check room availability

- Enter guest details (name, email, phone)

- Choose from available rooms

- System automatically calculates total amount

### 4. Check-in Guests

- Go to Reservations page

- Click "Check In" button for reserved guests

- Room status automatically updates to "Occupied"

- Guest status changes to "Checked In"

### 5. Check-out Guests

- Find checked-in guests in Reservations

- Click "Check Out" button

- System processes payment automatically

- Room status changes to "Needs Cleaning"

### 6. Search & Filter

#### 🔎Use search box to find reservations by:

- Guest name

- Room number

- Reservation ID

- Filter by status: Reserved, Checked In, Checked Out

## 💡Quick Tips:

- Check room availability before making reservations

- Search functionality helps find reservations quickly

- Status badges show current reservation state

- Action buttons change based on reservation status

- Auto-calculated totals based on stay duration

## 🚨Important Notes:

- Cannot cancel checked-in reservations

- Check-out date must be after check-in date

- Room availability is checked automatically

- Past dates are not allowed for check-in

- Data persists between server restarts

