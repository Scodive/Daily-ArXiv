import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Set style for publication quality plots
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['font.family'] = 'Arial'
plt.rcParams['axes.linewidth'] = 1.5
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['xtick.labelsize'] = 10
plt.rcParams['ytick.labelsize'] = 10
plt.rcParams['legend.fontsize'] = 10
plt.rcParams['figure.titlesize'] = 14

# Create data
data = {
    'Model': ['all-roberta-large-v1'] * 4 + ['sentence-t5-large'] * 4 + ['all-mpnet-base-v2'] * 4,
    'Repetitions': [1, 3, 5, 10] * 3,
    'ADE': [4.32, 3.87, 3.65, 3.78, 4.45, 4.02, 3.79, 3.91, 4.21, 3.76, 3.54, 3.68],
    'Collision Rate (%)': [9.8, 8.2, 7.2, 7.8, 10.2, 8.7, 7.5, 8.0, 9.5, 8.0, 7.1, 7.6],
    'Infraction Rate (%)': [8.5, 7.1, 6.5, 7.0, 8.9, 7.6, 6.8, 7.3, 8.3, 7.0, 6.4, 6.9],
    'F2 Score': [0.88, 0.90, 0.93, 0.91, 0.87, 0.89, 0.92, 0.90, 0.88, 0.91, 0.94, 0.92],
    'Improvement (%)': [0, 5.68, 9.09, 7.39, 0, 4.49, 8.05, 6.32, 0, 6.82, 10.71, 8.57]
}

df = pd.DataFrame(data)

def plot_metrics_trends():
    # Create subplots
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('Performance Trends with Different Repetition Counts', fontsize=16, y=0.95)
    
    # Customize the style
    for ax in axes.flat:
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.grid(True, linestyle='--', alpha=0.7)
    
    # 1. ADE trends
    for model in df['Model'].unique():
        model_data = df[df['Model'] == model]
        axes[0,0].plot(model_data['Repetitions'], model_data['ADE'], 
                      marker='o', label=model, linewidth=2)
    axes[0,0].set_title('Average Displacement Error (ADE)', pad=15)
    axes[0,0].set_xlabel('Number of Repetitions')
    axes[0,0].set_ylabel('ADE')
    axes[0,0].legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    
    # 2. Collision Rate trends
    for model in df['Model'].unique():
        model_data = df[df['Model'] == model]
        axes[0,1].plot(model_data['Repetitions'], model_data['Collision Rate (%)'], 
                      marker='o', label=model, linewidth=2)
    axes[0,1].set_title('Collision Rate', pad=15)
    axes[0,1].set_xlabel('Number of Repetitions')
    axes[0,1].set_ylabel('Collision Rate (%)')
    axes[0,1].legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    
    # 3. Infraction Rate trends
    for model in df['Model'].unique():
        model_data = df[df['Model'] == model]
        axes[1,0].plot(model_data['Repetitions'], model_data['Infraction Rate (%)'], 
                      marker='o', label=model, linewidth=2)
    axes[1,0].set_title('Infraction Rate', pad=15)
    axes[1,0].set_xlabel('Number of Repetitions')
    axes[1,0].set_ylabel('Infraction Rate (%)')
    axes[1,0].legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    
    # 4. F2 Score trends
    for model in df['Model'].unique():
        model_data = df[df['Model'] == model]
        axes[1,1].plot(model_data['Repetitions'], model_data['F2 Score'], 
                      marker='o', label=model, linewidth=2)
    axes[1,1].set_title('F2 Score', pad=15)
    axes[1,1].set_xlabel('Number of Repetitions')
    axes[1,1].set_ylabel('F2 Score')
    axes[1,1].legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    
    plt.tight_layout()
    plt.savefig('repetition_metrics_trends.png', dpi=300, bbox_inches='tight')
    plt.close()

def plot_improvement_trends():
    plt.figure(figsize=(10, 6))
    
    for model in df['Model'].unique():
        model_data = df[df['Model'] == model]
        plt.plot(model_data['Repetitions'], model_data['Improvement (%)'], 
                marker='o', label=model, linewidth=2)
    
    plt.title('Performance Improvement with Repetition Counts', pad=20)
    plt.xlabel('Number of Repetitions')
    plt.ylabel('Improvement Percentage (%)')
    
    # Customize style
    plt.gca().spines['top'].set_visible(False)
    plt.gca().spines['right'].set_visible(False)
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Add legend
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    
    plt.tight_layout()
    plt.savefig('repetition_improvement_trends.png', dpi=300, bbox_inches='tight')
    plt.close()

def plot_heatmap():
    # Create a pivot table for the improvement percentages
    pivot_data = df.pivot(index='Model', columns='Repetitions', values='Improvement (%)')
    
    plt.figure(figsize=(10, 6))
    sns.heatmap(pivot_data, annot=True, fmt='.1f', cmap='YlOrRd', 
                cbar_kws={'label': 'Improvement (%)'})
    
    plt.title('Performance Improvement Heatmap', pad=20)
    plt.xlabel('Number of Repetitions')
    plt.ylabel('Model')
    
    plt.tight_layout()
    plt.savefig('repetition_improvement_heatmap.png', dpi=300, bbox_inches='tight')
    plt.close()

if __name__ == "__main__":
    plot_metrics_trends()
    plot_improvement_trends()
    plot_heatmap() 