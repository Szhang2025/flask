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
# CREATE DATA TABLE
# =========================================================

def create_table(df):

    preview = df.head(100)

    return preview.to_html(
        classes="data-table",
        index=False
    )


# =========================================================
# CREATE COMMON PAGE DATA
# =========================================================

def get_page_data(df):

    numeric_variables, categorical_variables = (
        get_variable_types(df)
    )

    return {
        "rows": len(df),
        "columns": len(df.columns),
        "table": create_table(df),
        "numeric_variables": numeric_variables,
        "categorical_variables": categorical_variables,
        "all_variables": df.columns.tolist()
    }


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

    if "file" not in request.files:

        return "No file selected."

    file = request.files["file"]

    if file.filename == "":

        return "No file selected."

    if not allowed_file(
        file.filename
    ):

        return (
            "Only CSV and Excel files are allowed."
        )

    filename = secure_filename(
        file.filename
    )

    filepath = os.path.join(
        app.config["UPLOAD_FOLDER"],
        filename
    )

    try:

        file.save(filepath)

    except Exception as e:

        return (
            f"Error saving file: {e}"
        )

    try:

        df = read_data(
            filepath,
            filename
        )

    except Exception as e:

        return (
            f"Error reading file: {e}"
        )

    page_data = get_page_data(df)

    return render_template(
        "data.html",

        filename=filename,

        rows=page_data["rows"],

        columns=page_data["columns"],

        table=page_data["table"],

        numeric_variables=page_data[
            "numeric_variables"
        ],

        categorical_variables=page_data[
            "categorical_variables"
        ],

        all_variables=page_data[
            "all_variables"
        ],

        graph_type=None,

        graph_file=None,

        selected_variable=None,

        variable1=None,

        variable2=None,

        graph_type_two=None,

        graph_file_two=None,

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

    if not filename:

        return "Missing filename."

    if not variable:

        return (
            "Please select a variable."
        )

    if not graph_type:

        return (
            "Please select a graph."
        )

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

    try:

        df = read_data(
            filepath,
            filename
        )

    except Exception as e:

        return (
            f"Error reading data: {e}"
        )

    if variable not in df.columns:

        return (
            "Variable not found."
        )

    (
        numeric_variables,
        categorical_variables
    ) = get_variable_types(df)

    # -----------------------------------------------------
    # Validate graph
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
                "Bar chart requires a "
                "categorical variable."
            )

    else:

        return "Invalid graph type."

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
    # Create graph
    # -----------------------------------------------------

    plt.figure(
        figsize=(8, 5)
    )

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

    plt.tight_layout()

    plt.savefig(
        graph_path,
        dpi=150,
        bbox_inches="tight"
    )

    plt.close()

    # -----------------------------------------------------
    # Return page
    # -----------------------------------------------------

    page_data = get_page_data(df)

    return render_template(
        "data.html",

        filename=filename,

        rows=page_data["rows"],

        columns=page_data["columns"],

        table=page_data["table"],

        numeric_variables=page_data[
            "numeric_variables"
        ],

        categorical_variables=page_data[
            "categorical_variables"
        ],

        all_variables=page_data[
            "all_variables"
        ],

        graph_type=graph_type,

        graph_file=graph_filename,

        selected_variable=variable,

        variable1=None,

        variable2=None,

        graph_type_two=None,

        graph_file_two=None,

        error=None
    )


# =========================================================
# TWO-VARIABLE ANALYSIS
# =========================================================

@app.route(
    "/analyze-two",
    methods=["POST"]
)
def analyze_two():

    filename = request.form.get(
        "filename"
    )

    variable1 = request.form.get(
        "variable1"
    )

    variable2 = request.form.get(
        "variable2"
    )

    graph_type = request.form.get(
        "graph_type_two"
    )

    if not filename:

        return "Missing filename."

    if not variable1 or not variable2:

        return (
            "Please select two variables."
        )

    if variable1 == variable2:

        return (
            "Please select two different variables."
        )

    if not graph_type:

        return (
            "Please select a graph."
        )

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

    try:

        df = read_data(
            filepath,
            filename
        )

    except Exception as e:

        return (
            f"Error reading data: {e}"
        )

    if variable1 not in df.columns:

        return (
            f"Variable not found: {variable1}"
        )

    if variable2 not in df.columns:

        return (
            f"Variable not found: {variable2}"
        )

    (
        numeric_variables,
        categorical_variables
    ) = get_variable_types(df)

    type1 = (
        "numeric"
        if variable1 in numeric_variables
        else "categorical"
    )

    type2 = (
        "numeric"
        if variable2 in numeric_variables
        else "categorical"
    )

    # -----------------------------------------------------
    # Validate graph type
    # -----------------------------------------------------

    if graph_type == "scatterplot":

        if not (
            type1 == "numeric"
            and type2 == "numeric"
        ):

            return (
                "Scatterplot requires "
                "two numeric variables."
            )

    elif graph_type == "boxplot_two":

        if not (
            (
                type1 == "categorical"
                and type2 == "numeric"
            )
            or
            (
                type1 == "numeric"
                and type2 == "categorical"
            )
        ):

            return (
                "Side-by-side boxplot requires "
                "one categorical and one numeric variable."
            )

    elif graph_type == "grouped_bar":

        if not (
            type1 == "categorical"
            and type2 == "categorical"
        ):

            return (
                "Grouped bar chart requires "
                "two categorical variables."
            )

    else:

        return "Invalid graph type."

    # -----------------------------------------------------
    # Select useful columns and remove missing values
    # -----------------------------------------------------

    data = df[
        [variable1, variable2]
    ].dropna()

    if len(data) == 0:

        return (
            "There are no complete observations "
            "for the selected variables."
        )

    # -----------------------------------------------------
    # Create graph filename
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
    # Create graph
    # -----------------------------------------------------

    plt.figure(
        figsize=(8, 5)
    )

    # =====================================================
    # SCATTERPLOT
    # =====================================================

    if graph_type == "scatterplot":

        plt.scatter(
            data[variable1],
            data[variable2],
            alpha=0.7
        )

        plt.xlabel(
            variable1
        )

        plt.ylabel(
            variable2
        )

        plt.title(
            f"{variable2} vs. {variable1}"
        )

    # =====================================================
    # SIDE-BY-SIDE BOXPLOT
    # =====================================================

    elif graph_type == "boxplot_two":

        if type1 == "categorical":

            category = variable1
            numeric = variable2

        else:

            category = variable2
            numeric = variable1

        groups = []

        labels = []

        grouped = data.groupby(
            category,
            sort=False
        )

        for name, group in grouped:

            groups.append(
                group[numeric].values
            )

            labels.append(
                str(name)
            )

        plt.boxplot(
            groups,
            labels=labels
        )

        plt.xlabel(
            category
        )

        plt.ylabel(
            numeric
        )

        plt.title(
            f"{numeric} by {category}"
        )

        plt.xticks(
            rotation=45,
            ha="right"
        )

    # =====================================================
    # GROUPED BAR CHART
    # =====================================================

    elif graph_type == "grouped_bar":

        table = pd.crosstab(
            data[variable1],
            data[variable2]
        )

        table.plot(
            kind="bar",
            figsize=(8, 5)
        )

        plt.xlabel(
            variable1
        )

        plt.ylabel(
            "Frequency"
        )

        plt.title(
            f"{variable1} by {variable2}"
        )

        plt.xticks(
            rotation=45,
            ha="right"
        )

        plt.legend(
            title=variable2,
            bbox_to_anchor=(1.02, 1),
            loc="upper left"
        )

    plt.tight_layout()

    plt.savefig(
        graph_path,
        dpi=150,
        bbox_inches="tight"
    )

    plt.close()

    # -----------------------------------------------------
    # Return page
    # -----------------------------------------------------

    page_data = get_page_data(df)

    return render_template(
        "data.html",

        filename=filename,

        rows=page_data["rows"],

        columns=page_data["columns"],

        table=page_data["table"],

        numeric_variables=page_data[
            "numeric_variables"
        ],

        categorical_variables=page_data[
            "categorical_variables"
        ],

        all_variables=page_data[
            "all_variables"
        ],

        graph_type=None,

        graph_file=None,

        selected_variable=None,

        variable1=variable1,

        variable2=variable2,

        graph_type_two=graph_type,

        graph_file_two=graph_filename,

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
