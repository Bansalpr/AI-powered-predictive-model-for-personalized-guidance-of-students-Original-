$(document).ready(function() {
    $('#predictionForm').submit(function(event) {
        event.preventDefault(); // Prevent form from submitting traditionally

        // Collect data from form inputs
        const formData = {
            'Hours Studied': $('#hours_studied').val(),
            'Previous Scores_scaled': $('#previous_scores').val(),
            'Extracurricular Activities': $('#extracurricular_activities').val(),
            'Sleep Hours': $('#sleep_hours').val(),
            'Sample Question Papers Practiced': $('#question_papers').val()
        };

        // Send AJAX POST request to Flask API
        $.ajax({
            url: '/predict',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(formData),
            success: function(response) {
                // Display prediction result
                $('#predictionText').text(response.Prediction);
                $('#predictionResult').show();
            },
            error: function(xhr, status, error) {
                alert('Error: ' + error);
            }
        });
    });
});
