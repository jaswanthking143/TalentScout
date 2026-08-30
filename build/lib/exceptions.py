"""
exceptions.py
Custom exception hierarchy for the TalentScout Resume Analyzer.
"""


class TalentScoutError(Exception):
    """Base exception for all TalentScout errors."""
    pass


class InvalidFileFormatError(TalentScoutError):
    """Raised when a non-PDF file is supplied as input."""
    def __init__(self, filename: str):
        self.filename = filename
        super().__init__(f"Invalid file format: '{filename}'. Only .pdf files are accepted.")


class PDFExtractionError(TalentScoutError):
    """Raised when text cannot be extracted from a PDF (corrupt / scanned / empty)."""
    def __init__(self, filename: str, reason: str = ""):
        self.filename = filename
        msg = f"Failed to extract data from '{filename}'."
        if reason:
            msg += f" Reason: {reason}"
        super().__init__(msg)


class NoCandidateDataError(TalentScoutError):
    """Raised when the analyzer is run with zero candidates loaded."""
    def __init__(self):
        super().__init__("No candidates loaded. Please upload at least one resume PDF first.")


class EmptyRoleInputError(TalentScoutError):
    """Raised when the user clicks Analyze without entering a target role."""
    def __init__(self):
        super().__init__("Please enter a role to analyze candidates against.")