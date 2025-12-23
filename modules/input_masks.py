
class Masks():
    def validate_longitude(self, text):
        """Validate longitude input in real-time."""
        try:
            value = float(text)
            if value < -180.0 or value > 180.0:
                self.longitudeInput.setStyleSheet("QLineEdit { background-color: red; }")
            else:
                self.longitudeInput.setStyleSheet("")
        except ValueError:
            self.longitudeInput.setStyleSheet("QLineEdit { background-color: red; }")