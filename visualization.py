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

# Color palette for publication
COLORS = ['#2E86C1', '#E74C3C', '#27AE60', '#F39C12', '#8E44AD']
sns.set_palette(COLORS)

# Create data
data = {
    'Model': ['DriveGPT4', 'DriveGPT4', 'OpenEMMA', 'OpenEMMA', 'Sc-VLM', 'Sc-VLM', 
              'CALMM-Drive', 'CALMM-Drive', 'Ours', 'Ours'],
    'Uncertainty-Aware': ['No', 'No', 'No', 'No', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes'],
    'Dataset': ['NuScenes', 'Extreme Conditions'] * 5,
    'ADE': [4.32, 7.45, 4.15, 7.89, 3.87, 5.32, 3.72, 5.14, 3.54, 4.87],
    'Collision Rate (%)': [9.8, 18.6, 8.7, 20.1, 8.2, 12.4, 7.5, 11.8, 7.1, 10.2],
    'Infraction Rate (%)': [8.5, 14.9, 7.9, 16.3, 7.1, 9.8, 6.8, 9.2, 6.4, 8.5],
    'F2 Score': [0.88, 0.82, 0.90, 0.81, 0.91, 0.86, 0.92, 0.88, 0.94, 0.90]
}

df = pd.DataFrame(data)

def plot_metrics_comparison():
    # Create subplots
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('Performance Comparison Across Models', fontsize=16, y=0.95)
    
    # Customize the style
    for ax in axes.flat:
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.grid(True, linestyle='--', alpha=0.7)
    
    # 1. ADE comparison
    sns.barplot(data=df, x='Model', y='ADE', hue='Dataset', ax=axes[0,0], palette=['#2E86C1', '#E74C3C'])
    axes[0,0].set_title('Average Displacement Error (ADE)', pad=15)
    axes[0,0].set_xlabel('')
    axes[0,0].tick_params(axis='x', rotation=45)
    axes[0,0].legend(title='Dataset', bbox_to_anchor=(1.05, 1), loc='upper left')
    
    # 2. Collision Rate comparison
    sns.barplot(data=df, x='Model', y='Collision Rate (%)', hue='Dataset', ax=axes[0,1], palette=['#2E86C1', '#E74C3C'])
    axes[0,1].set_title('Collision Rate', pad=15)
    axes[0,1].set_xlabel('')
    axes[0,1].tick_params(axis='x', rotation=45)
    axes[0,1].legend(title='Dataset', bbox_to_anchor=(1.05, 1), loc='upper left')
    
    # 3. Infraction Rate comparison
    sns.barplot(data=df, x='Model', y='Infraction Rate (%)', hue='Dataset', ax=axes[1,0], palette=['#2E86C1', '#E74C3C'])
    axes[1,0].set_title('Infraction Rate', pad=15)
    axes[1,0].set_xlabel('')
    axes[1,0].tick_params(axis='x', rotation=45)
    axes[1,0].legend(title='Dataset', bbox_to_anchor=(1.05, 1), loc='upper left')
    
    # 4. F2 Score comparison
    sns.barplot(data=df, x='Model', y='F2 Score', hue='Dataset', ax=axes[1,1], palette=['#2E86C1', '#E74C3C'])
    axes[1,1].set_title('F2 Score', pad=15)
    axes[1,1].set_xlabel('')
    axes[1,1].tick_params(axis='x', rotation=45)
    axes[1,1].legend(title='Dataset', bbox_to_anchor=(1.05, 1), loc='upper left')
    
    plt.tight_layout()
    plt.savefig('metrics_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()

def plot_uncertainty_impact():
    # Calculate performance improvements
    uncertainty_models = df[df['Uncertainty-Aware'] == 'Yes']
    non_uncertainty_models = df[df['Uncertainty-Aware'] == 'No']
    
    metrics = ['ADE', 'Collision Rate (%)', 'Infraction Rate (%)', 'F2 Score']
    improvements = []
    
    for metric in metrics:
        if metric == 'F2 Score':
            improvement = (uncertainty_models[metric].mean() - non_uncertainty_models[metric].mean()) / non_uncertainty_models[metric].mean() * 100
        else:
            improvement = (non_uncertainty_models[metric].mean() - uncertainty_models[metric].mean()) / non_uncertainty_models[metric].mean() * 100
        improvements.append(improvement)
    
    plt.figure(figsize=(10, 6))
    bars = plt.bar(metrics, improvements, color='#2E86C1')
    plt.title('Performance Improvement with Uncertainty Awareness', pad=20)
    plt.ylabel('Improvement Percentage (%)')
    
    # Customize style
    plt.gca().spines['top'].set_visible(False)
    plt.gca().spines['right'].set_visible(False)
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Add value labels
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}%',
                ha='center', va='bottom')
    
    plt.tight_layout()
    plt.savefig('uncertainty_impact.png', dpi=300, bbox_inches='tight')
    plt.close()

def plot_dataset_comparison():
    # Calculate performance degradation in extreme conditions
    nuscenes = df[df['Dataset'] == 'NuScenes']
    extreme = df[df['Dataset'] == 'Extreme Conditions']
    
    metrics = ['ADE', 'Collision Rate (%)', 'Infraction Rate (%)', 'F2 Score']
    degradation = []
    
    for metric in metrics:
        if metric == 'F2 Score':
            deg = (nuscenes[metric].mean() - extreme[metric].mean()) / nuscenes[metric].mean() * 100
        else:
            deg = (extreme[metric].mean() - nuscenes[metric].mean()) / nuscenes[metric].mean() * 100
        degradation.append(deg)
    
    plt.figure(figsize=(10, 6))
    bars = plt.bar(metrics, degradation, color='#E74C3C')
    plt.title('Performance Change in Extreme Conditions', pad=20)
    plt.ylabel('Change Percentage (%)')
    
    # Customize style
    plt.gca().spines['top'].set_visible(False)
    plt.gca().spines['right'].set_visible(False)
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Add value labels
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}%',
                ha='center', va='bottom')
    
    plt.tight_layout()
    plt.savefig('dataset_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()

if __name__ == "__main__":
    plot_metrics_comparison()
    plot_uncertainty_impact()
    plot_dataset_comparison() 