document.getElementById('addCourseBtn').addEventListener('click', function() {
    document.getElementById('addCourseModal').style.display = 'block';
});

document.getElementById('cancelAddCourse').addEventListener('click', function() {
    document.getElementById('addCourseModal').style.display = 'none';
});

document.getElementById('addCourseForm').addEventListener('submit', function(event) {
    event.preventDefault();
    var formData = new FormData(this);
    fetch('/add_course', {
        method: 'POST',
        body: formData,
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message);
        location.reload();
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Failed to add course.');
    });
});