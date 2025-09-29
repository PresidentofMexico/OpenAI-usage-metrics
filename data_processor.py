import pandas as pd

def load_data(file_path):
    """Load usage metrics data from a CSV file."""
    return pd.read_csv(file_path)

def process_metrics(data):
    """Process OpenAI usage metrics data."""
    # Example processing: Calculate total usage
    total_usage = data['usage'].sum()
    return total_usage

def generate_summary(data):
    """Generate a summary of the usage metrics."""
    summary = {
        'total_usage': process_metrics(data),
        'average_usage': data['usage'].mean(),
        'max_usage': data['usage'].max(),
        'min_usage': data['usage'].min(),
    }
    return summary

if __name__ == "__main__":
    # Example usage
    file_path = 'usage_metrics.csv'  # Placeholder for the actual file path
    data = load_data(file_path)
    summary = generate_summary(data)
    print(summary)