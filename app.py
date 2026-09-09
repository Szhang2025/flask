from flask import Flask, render_template, request
import pandas as pd
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)


# =========================================================
# Configuration
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Maximum file size: 50 MB
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024

ALLOWED_EXTENSIONS = {"csv", "xlsx", "xls"}


# =========================================================
# Check whether the file type is allowed
# =========================================================

def allowed_file(filename):

    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )


# =========================================================
# Read CSV or Excel file
# =========================================================

def read_data(filepath, filename):

    extension = filename.rsplit(".", 1)[1].lower()

    if extension == "csv":

        try:
            df = pd.read_csv(filepath)

        except UnicodeDecodeError:

            df = pd.read_csv(
                filepath,
                encoding="latin1"
            )

    elif extension == "xlsx":

        df = pd.read_excel(
            filepath,
            engine="openpyxl"
        )

    elif extension == "xls":

        df = pd.read_excel(filepath)

    else:

        raise ValueError(
            "Unsupported file type."
        )

    return df


# =========================================================
# Determine variable types
# =========================================================

def get_variable_types(df):

    numeric_variables = (
        df.select_dtypes(include=["number"])
        .columns
        .tolist()
    )

    categorical_variables = (
        df.select_dtypes(
            include=["object", "category", "bool"]
        )
        .columns
        .tolist()
    )

    return (
        numeric_variables,
        categorical_variables
    )


# =========================================================
# HOME PAGE
# =========================================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# =========================================================
# UPLOAD DATA
# =========================================================

@app.route(
    "/upload",
    methods=["POST"]
)
def upload():

    print()
    print("=" * 60)
    print("UPLOAD REQUEST RECEIVED")
    print("=" * 60)


    # -----------------------------------------------------
    # Check whether a file was submitted
    # -----------------------------------------------------

    if "file" not in request.files:

        print("ERROR: No file field.")

        return "No file selected."


    file = request.files["file"]


    # -----------------------------------------------------
    # Check filename
    # -----------------------------------------------------

    if file.filename == "":

        print("ERROR: Empty filename.")

        return "No file selected."


    # -----------------------------------------------------
    # Check file type
    # -----------------------------------------------------

    if not allowed_file(file.filename):

        print("ERROR: File type not allowed.")

        return (
            "Only CSV and Excel files are allowed."
        )


    # -----------------------------------------------------
    # Make filename safe
    # -----------------------------------------------------

    filename = secure_filename(
        file.filename
    )


    filepath = os.path.join(
        app.config["UPLOAD_FOLDER"],
        filename
    )


    print("Filename:")
    print(filename)

    print()

    print("File path:")
    print(filepath)


    # -----------------------------------------------------
    # Save uploaded file
    # -----------------------------------------------------

    try:

        file.save(filepath)

        print()
        print("File saved successfully.")

    except Exception as e:

        print()
        print("ERROR SAVING FILE:")
        print(e)

        return (
            f"Error saving file: {e}"
        )


    # -----------------------------------------------------
    # Read the data
    # -----------------------------------------------------

    try:

        df = read_data(
            filepath,
            filename
        )

        print()
        print("Data loaded successfully.")

    except Exception as e:

        print()
        print("ERROR READING DATA:")
        print(e)

        return (
            f"Error reading file: {e}"
        )


    # -----------------------------------------------------
    # Dataset dimensions
    # -----------------------------------------------------

    rows = len(df)

    columns = len(df.columns)


    print()
    print("Rows:", rows)
    print("Columns:", columns)


    # -----------------------------------------------------
    # Variable names
    # -----------------------------------------------------

    print()
    print("Variables:")

    for column in df.columns:

        print(" -", column)


    # -----------------------------------------------------
    # Determine variable types
    # -----------------------------------------------------

    (
        numeric_variables,
        categorical_variables
    ) = get_variable_types(df)


    print()
    print("Numeric variables:")

    for variable in numeric_variables:

        print(" -", variable)


    print()
    print("Categorical variables:")

    for variable in categorical_variables:

        print(" -", variable)


    # -----------------------------------------------------
    # Create data preview
    # -----------------------------------------------------

    preview = df.head(100)

    table = preview.to_html(
        classes="data-table",
        index=False
    )


    # -----------------------------------------------------
    # Send everything to data.html
    # -----------------------------------------------------

    print()
    print("Sending data to data.html...")

    print("=" * 60)
    print()


    return render_template(
        "data.html",

        filename=filename,

        rows=rows,

        columns=columns,

        table=table,

        numeric_variables=numeric_variables,

        categorical_variables=categorical_variables
    )


# =========================================================
# Run Flask
# =========================================================

if __name__ == "__main__":

    print()
    print("=" * 60)
    print("FLASK DATA ANALYSIS APP")
    print("=" * 60)

    print()
    print("Application folder:")
    print(BASE_DIR)

    print()
    print("Upload folder:")
    print(UPLOAD_FOLDER)

    print()
    print("Open your browser:")
    print("http://127.0.0.1:5000")

    print()
    print("=" * 60)
    print()

    app.run(
        debug=True
    )