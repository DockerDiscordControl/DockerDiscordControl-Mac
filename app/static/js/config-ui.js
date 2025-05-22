// Other initialization code...

// Add handler for Docker container list refresh button
$("#refresh-docker-list").on("click", function() {
    const $button = $(this);
    const $icon = $button.find("i");
    const $statusText = $("#cache-status-text");
    
    // Show loading state
    $button.prop("disabled", true);
    $icon.addClass("spin");
    $statusText.text("Refreshing container list...").show();
    
    // Make AJAX request to refresh containers
    $.ajax({
        url: "/refresh_containers",
        method: "POST",
        dataType: "json",
        success: function(response) {
            if (response.success) {
                // Reload the page to show updated containers
                window.location.reload();
            } else {
                $statusText.text("Error: " + (response.message || "Failed to refresh container list")).show();
                setTimeout(() => $statusText.fadeOut(), 5000);
            }
        },
        error: function() {
            $statusText.text("Error: Could not connect to server").show();
            setTimeout(() => $statusText.fadeOut(), 5000);
        },
        complete: function() {
            // Reset button state
            $button.prop("disabled", false);
            $icon.removeClass("spin");
        }
    });
});

// Add spin animation for the refresh icon
$("<style>")
    .text("@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }" +
          ".spin { animation: spin 1s linear infinite; }")
    .appendTo("head");

// Other initialization code... 