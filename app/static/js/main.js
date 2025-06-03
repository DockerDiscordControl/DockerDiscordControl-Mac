                    const result = await response.json();
                    
                    if (result.success) {
                        // Clear unsaved changes flag
                        hasUnsavedChanges = false;
                        
                        showAlert('Configuration saved successfully!', 'success');
                        // Reload the page to show updated configuration
                        setTimeout(() => {
                            window.location.reload();
                        }, 1000);
                    } else {
                        // Check for permission errors
                        if (result.permission_errors && result.permission_errors.length > 0) {
                            let errorMessage = 'Configuration files are not writable:\n\n';
                            result.permission_errors.forEach(error => {
                                errorMessage += `• ${error}\n`;
                            });
                            errorMessage += '\nPlease check the server logs for instructions on how to fix file permissions.';
                            showAlert(errorMessage, 'danger');
                        } else {
                            showAlert(result.message || 'Failed to save configuration', 'danger');
                        }
                    } 