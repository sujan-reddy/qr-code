document.addEventListener('DOMContentLoaded', (event) => {
    function fetchLatestQRCode() {
        fetch('/get_latest_qr')
            .then(response => response.json())
            .then(data => {
                document.getElementById('qr-result').innerText = data.qr_code || 'None';
            });
    }

    // Fetch the latest QR code every second
    setInterval(fetchLatestQRCode, 1000);
});
