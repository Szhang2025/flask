```python
from flask import Flask, render_template, request
import pandas as pd
import os
import uuid
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from werkzeug.utils import secure_filename


app = Flask(__name__)


# =========================================================
# CONFIGURATION
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

UPLOAD_FOLDER = os.path.join(
    BASE_DIR,
    "uploads"
)

PLOT_FOLDER = os.path.join(
    BASE_DIR,
    "static",
    "plots"
)

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PLOT_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Maximum upload size: 50 MB
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024

ALLOWED_EXTENSIONS = {
    "csv",
    "xlsx",
    "xls"
}


# =========================================================
# CHECK FILE TYPE
# =========================================================

def allowed_file(filename):

    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )


# =========================================================
# READ DATA
# =========================================================

def read_data(filepath, filename):

    extension = filename.rsplit(
        ".",
        1
    )[1].lower()


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

        df = pd.read_excel(
            filepath
        )


    else:

        raise ValueError(
            "Unsupported file type."
        )


    return df


# =========================================================
# DETERMINE VARIABLE TYPES
# =========================================================

def get_variable_types(df):

    numeric_variables = (
        df
        .select_dtypes(
            include=["number"]
        )
        .columns
        .tolist()
    )


    categorical_variables = (
        df
        .select_dtypes(
            include=[
                "object",
                "category",
                "bool"
            ]
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

    # -----------------------------------------------------
    # Check file
    # -----------------------------------------------------

    if "file" not in request.files:

        return "No file selected."


    file = request.files["file"]


    if file.filename == "":

        return "No file selected."


    # -----------------------------------------------------
    # Check extension
    # -----------------------------------------------------

    if not allowed_file(
        file.filename
    ):

        return (
            "Only CSV and Excel files are allowed."
        )


    # -----------------------------------------------------
    # Secure filename
    # -----------------------------------------------------

    filename = secure_filename(
        file.filename
    )


    filepath = os.path.join(
        app.config["UPLOAD_FOLDER"],
        filename
    )


    # -----------------------------------------------------
    # Save file
    # -----------------------------------------------------

    try:

        file.save(filepath)

    except Exception as e:

        return (
            f"Error saving file: {e}"
        )


    # -----------------------------------------------------
    # Read data
    # -----------------------------------------------------

    try:

        df = read_data(
            filepath,
            filename
        )

    except Exception as e:

        return (
            f"Error reading file: {e}"
        )


    # -----------------------------------------------------
    # Dataset information
    # -----------------------------------------------------

    rows = len(df)

    columns = len(df.columns)


    (
        numeric_variables,
        categorical_variables
    ) = get_variable_types(df)


    # -----------------------------------------------------
    # Preview
    # -----------------------------------------------------

    preview = df.head(100)


    table = preview.to_html(
        classes="data-table",
        index=False
    )


    # -----------------------------------------------------
    # Results page
    # -----------------------------------------------------

    return render_template(

        "data.html",

        filename=filename,

        rows=rows,

        columns=columns,

        table=table,

        numeric_variables=numeric_variables,

        categorical_variables=categorical_variables,

        all_variables=df.columns.tolist(),

        graph_type=None,

        graph_file=None,

        selected_variable=None,

        error=None
    )


# =========================================================
# ONE-VARIABLE ANALYSIS
# =========================================================

@app.route(
    "/analyze",
    methods=["POST"]
)
def analyze():

    filename = request.form.get(
        "filename"
    )

    variable = request.form.get(
        "variable"
    )

    graph_type = request.form.get(
        "graph_type"
    )


    # -----------------------------------------------------
    # Validate input
    # -----------------------------------------------------

    if not filename:

        return (
            "Missing filename."
        )


    if not variable:

        return (
            "Please select a variable."
        )


    if not graph_type:

        return (
            "Please select a graph."
        )


    # -----------------------------------------------------
    # Find uploaded file
    # -----------------------------------------------------

    filepath = os.path.join(
        app.config["UPLOAD_FOLDER"],
        filename
    )


    if not os.path.exists(filepath):

        return (
            "The uploaded file is no longer "
            "available. Please upload the "
            "data again."
        )


    # -----------------------------------------------------
    # Read data
    # -----------------------------------------------------

    try:

        df = read_data(
            filepath,
            filename
        )

    except Exception as e:

        return (
            f"Error reading data: {e}"
        )


    # -----------------------------------------------------
    # Check variable
    # -----------------------------------------------------

    if variable not in df.columns:

        return (
            "Variable not found."
        )


    # -----------------------------------------------------
    # Variable types
    # -----------------------------------------------------

    (
        numeric_variables,
        categorical_variables
    ) = get_variable_types(df)


    # -----------------------------------------------------
    # Validate graph type
    # -----------------------------------------------------

    if graph_type in [
        "histogram",
        "boxplot"
    ]:

        if variable not in numeric_variables:

            return (
                "Histogram and boxplot "
                "require a numeric variable."
            )


    elif graph_type == "barplot":

        if variable not in categorical_variables:

            return (
                "Bar chart requires "
                "a categorical variable."
            )


    else:

        return (
            "Invalid graph type."
        )


    # -----------------------------------------------------
    # Remove missing values
    # -----------------------------------------------------

    data = df[variable].dropna()


    if len(data) == 0:

        return (
            "The selected variable "
            "contains no usable data."
        )


    # -----------------------------------------------------
    # Unique graph filename
    # -----------------------------------------------------

    graph_filename = (
        str(uuid.uuid4())
        + ".png"
    )


    graph_path = os.path.join(
        PLOT_FOLDER,
        graph_filename
    )


    # -----------------------------------------------------
    # Create figure
    # -----------------------------------------------------

    plt.figure(
        figsize=(8, 5)
    )


    # =====================================================
    # HISTOGRAM
    # =====================================================

    if graph_type == "histogram":

        plt.hist(
            data,
            bins=20,
            edgecolor="black"
        )

        plt.xlabel(
            variable
        )

        plt.ylabel(
            "Frequency"
        )

        plt.title(
            f"Histogram of {variable}"
        )


    # =====================================================
    # BOXPLOT
    # =====================================================

    elif graph_type == "boxplot":

        plt.boxplot(
            data
        )

        plt.ylabel(
            variable
        )

        plt.title(
            f"Boxplot of {variable}"
        )


    # =====================================================
    # BAR CHART
    # =====================================================

    elif graph_type == "barplot":

        counts = (
            data
            .astype(str)
            .value_counts()
            .sort_values(
                ascending=False
            )
        )


        counts.plot(
            kind="bar"
        )


        plt.xlabel(
            variable
        )

        plt.ylabel(
            "Frequency"
        )

        plt.title(
            f"Bar Chart of {variable}"
        )


        plt.xticks(
            rotation=45,
            ha="right"
        )


    # -----------------------------------------------------
    # Save graph
    # -----------------------------------------------------

    plt.tight_layout()


    plt.savefig(
        graph_path,
        dpi=150,
        bbox_inches="tight"
    )


    plt.close()


    # -----------------------------------------------------
    # Data preview
    # -----------------------------------------------------

    preview = df.head(100)


    table = preview.to_html(
        classes="data-table",
        index=False
    )


    # -----------------------------------------------------
    # Display results
    # -----------------------------------------------------

    return render_template(

        "data.html",

        filename=filename,

        rows=len(df),

        columns=len(df.columns),

        table=table,

        numeric_variables=numeric_variables,

        categorical_variables=categorical_variables,

        all_variables=df.columns.tolist(),

        graph_type=graph_type,

        graph_file=graph_filename,

        selected_variable=variable,

        error=None
    )


# =========================================================
# RUN APPLICATION
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
    print("Open your browser:")
    print("http://127.0.0.1:5000")

    print()
    print("=" * 60)
    print()


    app.run(
        debug=True
    )
```
