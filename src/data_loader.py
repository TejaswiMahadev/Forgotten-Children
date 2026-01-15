import pandas as pd
import glob
import os
from src.data_validator import DataValidator
from src.data_cleaner import DataCleaner

class UIDAIDataLoader:
    def __init__(self, base_path):
        self.base_path = base_path
        self.data_dirs = {
            'enrollment': 'Aadhar_Enrollment_Data',
            'demographic': 'Aadhar_Demographic_Data',
            'biometric': 'Aadhar_Biometric_Data'
        }

    def load_dataset(self, category):
        """Loads, validates, and cleans all CSV files in a category directory."""
        if category not in self.data_dirs:
            raise ValueError(f"Invalid category: {category}")
        
        dir_path = os.path.join(self.base_path, self.data_dirs[category])
        all_files = glob.glob(os.path.join(dir_path, "*.csv"))
        
        df_list = []
        for filename in all_files:
            try:
                df = pd.read_csv(filename)
                # Add district name from filename for tracking
                district = os.path.basename(filename).replace('.csv', '').title()
                df['file_district'] = district
                df_list.append(df)
            except Exception as e:
                print(f"Error loading {filename}: {e}")
            
        if not df_list:
            return pd.DataFrame()
            
        combined_df = pd.concat(df_list, ignore_index=True)
        
        # Validate (FR-1.1)
        validation_report = DataValidator.validate(combined_df, category)
        if not validation_report['is_valid']:
            print(f"Validation errors for {category}: {validation_report['errors']}")
            # In a production system, we might halt here, but for a hackathon we proceed with cleaning
            
        # Clean (FR-1.2)
        cleaned_df = DataCleaner.clean(combined_df, category)
        
        return cleaned_df

if __name__ == "__main__":
    # Quick test
    import sys
    sys.path.append(os.getcwd())
    loader = UIDAIDataLoader(os.getcwd())
    enrollment_data = loader.load_dataset('enrollment')
    print("Enrollment Data Sample:")
    print(enrollment_data.head())
