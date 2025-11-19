import streamlit as st
import os
import glob
import pandas as pd  # Import pandas for data loading

# --- Configuration and Setup ---

# Set the title of the Streamlit application
st.title("CSV File Processor 📊")

# Define the directory to scan for CSV files
# NOTE: The 'output' directory must exist and contain CSV files for this to work
data_directory = 'output'
csv_files = glob.glob(os.path.join(data_directory, "*.csv"))

# --- State Management Initialization ---

# Initialize session state variables if they don't exist
if 'file_selected' not in st.session_state:
    # Tracks if the user has confirmed a file selection
    st.session_state.file_selected = False
if 'selected_file_path' not in st.session_state:
    # Stores the path of the confirmed file
    st.session_state.selected_file_path = None
if 'dataframe' not in st.session_state:
    # Stores the loaded dataframe
    st.session_state.dataframe = None


# --- Function to Handle Processing ---

def load_and_process_file(file_path):
    """Loads the CSV, stores it in state, and transitions to the processing phase."""
    try:
        # Load the CSV file into a pandas DataFrame
        df = pd.read_csv(file_path)

        # Update session state to reflect the transition
        st.session_state.file_selected = True
        st.session_state.selected_file_path = file_path
        st.session_state.dataframe = df

        # NOTE: A simple 'success' message isn't needed here
        # because the app will re-run and show the new content.

    except FileNotFoundError:
        st.error(f"File not found: {file_path}")
    except pd.errors.EmptyDataError:
        st.error(f"The file **{file_path}** is empty.")
    except Exception as e:
        st.error(f"An error occurred while loading the file: {e}")


# --- Application Flow Control ---

if not csv_files:
    # Handle the case where no CSV files are found
    st.error(f"No CSV files found in the directory: **{os.path.abspath(data_directory)}**")

elif not st.session_state.file_selected:
    # --- 1. File Selection Phase (Initial state) ---

    st.markdown("Use the radio button to select a file and the button to confirm your choice.")

    # Get the currently selected file path from the radio button
    # Note: This is *not* the confirmed file yet, just the one highlighted
    tentative_selection = st.radio(
        "**Select a CSV file to process:**",
        csv_files
    )

    st.write(f"You have tentatively selected: **{tentative_selection}**")

    # The button calls the function which updates the state and triggers a rerun
    if st.button("Process Selected File", key="process"):
        if tentative_selection:
            # Call the function with the path from the radio button
            load_and_process_file(tentative_selection)
        else:
            st.warning("Please select a file before processing.")

else:
    # Check if the DataFrame exists and has data
    if 'dataframe' in st.session_state and st.session_state.dataframe is not None and not st.session_state.dataframe.empty:

        df = st.session_state.dataframe
        total_rows = len(df)

        st.success(f"✅ Data loaded successfully for file: **{st.session_state.selected_file_path}**")

        # --- Date/Row Range Selection ---
        st.subheader("Filter Data Range")

        # 1. Define the min, max, and default values for the slider
        min_row = 0
        max_row = total_rows - 1  # Last index is total_rows - 1

        # 2. Initialize or retrieve the range from session_state
        if 'row_range' not in st.session_state:
            st.session_state.row_range = (min_row, max_row)

        # 3. Create the slider. The key is necessary to connect it to session_state.
        selected_range = st.slider(
            "Select Row Range (Inclusive)",
            min_value=min_row,
            max_value=max_row,
            value=st.session_state.row_range,
            step=1,
            key='row_range_slider'  # Key connects widget value to session_state['row_range_slider']
        )

        # Update session state with the new selected range
        st.session_state.row_range = selected_range

        # Get the start and end indices
        start_row_index = selected_range[0]
        end_row_index = selected_range[1]

        # Filter the DataFrame based on the selected indices
        # We use .iloc to select rows by their integer position
        filtered_df = df.iloc[start_row_index: end_row_index + 1]  # +1 because slicing is exclusive at the end

        # --- Data Line Chart Display ---
        st.subheader("Data Line Chart Preview")

        try:
            # Filter the (already row-filtered) DataFrame to include only numeric columns
            numeric_df = filtered_df.select_dtypes(include=['number'])

            if not numeric_df.empty:
                # Display the line chart for the selected range and numeric columns
                #st.line_chart(numeric_df)
                st.write(
                    f"Displaying **{len(numeric_df)}** rows (Rows **{start_row_index}** to **{end_row_index}**) across **{len(numeric_df.columns)}** numeric columns.")
            else:
                st.warning("⚠️ The selected range contains no numeric data to display a line chart.")

        except Exception as e:
            st.error(f"⚠️ An error occurred while plotting: {e}")

        st.markdown("---")

        # --- Filtered Data Summary Table ---
        st.subheader("Filtered Data Summary Table")

        if not numeric_df.empty:
            try:
                summary_df = numeric_df.agg(['mean', 'min', 'max']).T.reset_index()
                # Rename the columns for better display
                summary_df.columns = ['Dataset Name', 'Average Value', 'Minimal Value', 'Maximal Value']
#                summary_df['Select'] = False  # Initialize the selection column

                summary_df['Select'] = (summary_df['Minimal Value'] != summary_df['Maximal Value'])
                edited_df = st.data_editor(
                    summary_df,
                    width="stretch",
                    column_config={
                        "Select": st.column_config.CheckboxColumn(
                            "Select",  # Column Header
                            help="Select the dataset for further action",
                            default=False,
                            # 'Select' is the column name in summary_df
                        ),
                        # Optional: Format other columns if st.data_editor is used
                        "Average Value": st.column_config.NumberColumn(format="%.2f"),
                        "Minimal Value": st.column_config.NumberColumn(format="%.2f"),
                        "Maximal Value": st.column_config.NumberColumn(format="%.2f"),
                    },
                    disabled=['Dataset Name', 'Average Value', 'Minimal Value', 'Maximal Value'],
                    # Disable editing of summary data
                    hide_index=True
                )

                selected_rows = edited_df[edited_df['Select']]

            except Exception as e:
                st.error(f"⚠️ An error occurred while generating the summary table: {e}")
        else:
            st.info("No numeric data to summarize in the selected range.")

        st.markdown("---")

        # Add a button to go back to the selection screen
        if st.button("Select a different file", key="selectDifferent2"):
            # Reset the state variables to revert to the selection phase
            st.session_state.file_selected = False
            st.session_state.selected_file_path = None
            st.session_state.dataframe = None
            # Streamlit automatically re-runs after a button click
    else:
        st.error("Data is not loaded or is empty.")

    # The following lines are outside the main 'if' block and should likely be updated/adjusted
    # or wrapped in a conditional check for st.session_state.dataframe existence.
    if 'dataframe' in st.session_state and st.session_state.dataframe is not None:
        st.write(f"Number of rows: {len(st.session_state.dataframe)}")
        # st.write(f"Number of columns: {len(st.session_state.dataframe.columns)}")

    st.markdown("---")

    # Add a button to go back to the selection screen
    if st.button("Select a different file", key="selectDifferent"):
        # Reset the state variables to revert to the selection phase
        st.session_state.file_selected = False
        st.session_state.selected_file_path = None
        st.session_state.dataframe = None
        # Streamlit automatically re-runs after a button click,
        # and the 'elif not st.session_state.file_selected:' block will run next.