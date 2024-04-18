document.addEventListener('DOMContentLoaded', function() {
    var fileInput = document.getElementById('fileInput');
    var imagePreview = document.getElementById('imagePreview');
    var uploadBtn = document.getElementById('uploadBtn');
    var attendanceBtn = document.getElementById('attendanceBtn');
    var retakeAttendanceBtn = document.getElementById('retakeAttendanceBtn');
    var saveChangesBtn = document.getElementById('saveChangesBtn');
    var downloadCsv = document.getElementById('downloadCsv');
    var uploadMessage = document.getElementById('uploadMessage');
    var attendanceTableBody = document.getElementById('attendanceTableBody');

    fileInput.addEventListener('change', function(event) {
        var file = event.target.files[0];
        var reader = new FileReader();
        reader.onload = function(e) {
            imagePreview.src = e.target.result;
            imagePreview.style.display = 'block';
        };
        reader.readAsDataURL(file);
    });

    uploadBtn.addEventListener('click', function() {
        var formData = new FormData(document.getElementById('uploadForm'));
        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.file_url) {
                attendanceBtn.style.display = 'inline';
                uploadMessage.textContent = 'Image uploaded successfully!';
            } else {
                uploadMessage.textContent = 'Failed to upload the image.';
            }
        })
        .catch(error => {
            console.error('Error:', error);
            uploadMessage.textContent = 'An error occurred during image upload.';
        });
    });

    attendanceBtn.addEventListener('click', function() {
        var formData = new FormData(document.getElementById('uploadForm'));
        fetch('/take_attendance', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Attendance request failed');
            }
            return response.json();
        })
        .then(data => {
            if (data.annotated_image_url && data.attendance_csv_url) {
                imagePreview.src = data.annotated_image_url;
                downloadCsv.href = data.attendance_csv_url;
                downloadCsv.style.display = 'inline';
                displayCsvAsTable(data.attendance_csv_url);
                uploadMessage.textContent = 'Attendance taken successfully!';
            } else {
                uploadMessage.textContent = 'Failed to take attendance.';
            }
        })
        .catch(error => {
            console.error('Error:', error);
            uploadMessage.textContent = 'An error occurred during attendance taking.';
        });
    });

    retakeAttendanceBtn.addEventListener('click', function() {
        // Clear the existing attendance data and reset the form
        attendanceTableBody.innerHTML = '';
        downloadCsv.style.display = 'none';
        saveChangesBtn.style.display = 'none';
        uploadMessage.textContent = '';
        document.getElementById('uploadForm').reset();
    });

    saveChangesBtn.addEventListener('click', function() {
        var rows = attendanceTableBody.getElementsByTagName('tr');
        var csvData = '';
        for (var i = 0; i < rows.length; i++) {
            var cells = rows[i].getElementsByTagName('td');
            var rowData = [];
            for (var j = 0; j < cells.length; j++) {
                rowData.push(cells[j].textContent);
            }
            csvData += rowData.join(',') + '\n';
        }
        var courseId = document.querySelector('input[name="course_id"]').value;
        var selectedDate = document.querySelector('input[name="selected_date"]').value;
        var formData = new FormData();
        formData.append('csv_data', csvData);
        formData.append('course_id', courseId);
        formData.append('selected_date', selectedDate);
        fetch('/save_attendance', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            uploadMessage.textContent = 'Changes saved successfully!';
        })
        .catch(error => {
            console.error('Error:', error);
            uploadMessage.textContent = 'Failed to save changes.';
        });
    });

    function displayCsvAsTable(csvUrl) {
        fetch(csvUrl)
        .then(response => response.text())
        .then(csvData => {
            var rows = csvData.trim().split('\n');
            attendanceTableBody.innerHTML = '';
            rows.forEach(function(row, index) {
                var cells = row.split(',');
                var newRow = document.createElement('tr');
                cells.forEach(function(cell, cellIndex) {
                    var newCell = document.createElement('td');
                    newCell.contentEditable = (cellIndex === 1);
                    newCell.textContent = cell;
                    newRow.appendChild(newCell);
                });
                attendanceTableBody.appendChild(newRow);
            });
            saveChangesBtn.style.display = 'inline';
        })

        .catch(error => {
            console.error('Error:', error);
            uploadMessage.textContent = 'Failed to display attendance table.';
        });
    }
});