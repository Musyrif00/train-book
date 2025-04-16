const socket = io();
const clientId = Math.random().toString(36).substring(2);
let selectedSeat = null;
let bookingConfirmed = false;

const seatMap = document.getElementById('seat-map');
const controls = document.getElementById('controls');
const summary = document.getElementById('summary');

function renderSeats() {
    seatMap.innerHTML = '';
    for (let coach = 1; coach <= 6; coach++) {
        const coachDiv = document.createElement('div');
        coachDiv.className = 'mb-4';
        coachDiv.innerHTML = `<h3 class="text-lg font-bold">Coach C${coach}</h3>`;
        const seatsDiv = document.createElement('div');
        seatsDiv.className = 'flex flex-wrap';
        for (let seat = 1; seat <= 20; seat++) {
            const seatId = `C${coach}-S${seat}`;
            const button = document.createElement('button');
            button.className = `w-12 h-12 m-1 rounded ${
                seats[seatId]?.status === 'available' ? 'bg-green-500' :
                seats[seatId]?.status === 'locked' ? 'bg-yellow-500' :
                'bg-red-500'
            } ${selectedSeat === seatId ? 'ring-2 ring-blue-500' : ''}`;
            button.textContent = seatId;
            button.disabled = seats[seatId]?.status === 'booked';
            button.onclick = () => handleSeatClick(seatId);
            seatsDiv.appendChild(button);
        }
        coachDiv.appendChild(seatsDiv);
        seatMap.appendChild(coachDiv);
    }
}

function renderControls() {
    controls.innerHTML = selectedSeat && !bookingConfirmed
        ? `<button class="px-4 py-2 bg-blue-500 text-white rounded" onclick="confirmBooking()">Confirm Booking</button>`
        : '';
}

function renderSummary(bookingId) {
    if (bookingConfirmed && bookingId) {
        summary.innerHTML = `
            <div class="p-4 bg-gray-100 rounded">
                <h2 class="text-xl font-bold">Booking Summary</h2>
                <p><strong>Train Number:</strong> T123</p>
                <p><strong>Departure Time:</strong> 10:00 AM</p>
                <p><strong>Arrival Time:</strong> 6:00 PM</p>
                <p><strong>Seat:</strong> ${selectedSeat}</p>
                <p><strong>Total Amount:</strong> $50</p>
                <a href="/receipt/${bookingId}" class="inline-block mt-2 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">View Receipt</a>
            </div>
        `;
    }
}

const seats = {};
for (let coach = 1; coach <= 6; coach++) {
    for (let seat = 1; seat <= 20; seat++) {
        seats[`C${coach}-S${seat}`] = { status: 'available', user: null };
    }
}

function handleSeatClick(seatId) {
    if (seats[seatId].status === 'available') {
        if (selectedSeat) {
            socket.emit('unlockSeat', { seatId: selectedSeat, clientId });
        }
        socket.emit('lockSeat', { seatId, clientId });
        selectedSeat = seatId;
    }
    renderControls();
}

function confirmBooking() {
    if (selectedSeat) {
        socket.emit('confirmBooking', { seatId: selectedSeat, clientId });
    }
}

socket.on('seatUpdate', ({ seatId, status, bookingId }) => {
    if (seatId in seats) {
        seats[seatId].status = status;
        if (status === 'available') seats[seatId].user = null;
        if (status === 'booked' && seatId === selectedSeat) {
            bookingConfirmed = true;
            renderSummary(bookingId);
        }
        renderSeats();
        renderControls();
    }
});

socket.on('connect', () => {
    console.log('Socket.IO connected');
    renderSeats();
});

socket.on('connect_error', (error) => {
    console.error('Socket.IO connection error:', error);
});