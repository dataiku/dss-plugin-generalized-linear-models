import logging
import pandas as pd
from logging_assist.logging import logger

class LiftChartFormatter:
    
    def __init__(self, model_retriever, data_handler):
        self.model_retriever = model_retriever
        self.data_handler = data_handler

        
    def _process_set(self, dataset, nb_bins, dataset_type):
        """
        Processes a dataset to calculate lift chart metrics.

        Args:
            dataset (pd.DataFrame): The dataset to process.
            nb_bins (int): Number of bins to divide the data into.
            dataset_type (str): Type of dataset ('train' or 'test').

        Returns:
            pd.DataFrame: Processed lift chart data.
        """
        logger.debug(f'Processing {dataset_type} dataset.')
        
        try:
            tempdata = self.data_handler.sort_and_cumsum_exposure(dataset, self.model_retriever.exposure_columns)
            binned_data = self.data_handler.bin_data(tempdata, nb_bins)
            new_data = dataset.join(binned_data[['bin']], how='inner')
            lift_chart_data = self.data_handler.aggregate_metrics_by_bin(new_data, self.model_retriever.exposure_columns, self.model_retriever.target_column)
            
            lift_chart_data.columns = ['Category', 'Value', 'observedAverage', 'fittedAverage']
            lift_chart_data['dataset'] = dataset_type
            
            logger.debug(f'{dataset_type} dataset processed successfully.')
            return lift_chart_data
        
        except Exception as e:
            logger.error(f'Error processing {dataset_type} dataset: {e}')
            raise
            
    def _combine_and_format_data(self, train_data, test_data):
        """
        Combines and formats the lift chart data from train and test datasets.

        Args:
            train_data (pd.DataFrame): The lift chart data for the training set.
            test_data (pd.DataFrame): The lift chart data for the test set.

        Returns:
            pd.DataFrame: The combined and formatted lift chart data.
        """
        logger.debug('Combining and formatting lift chart data.')

        combined_data = train_data.append(test_data)
        combined_data.columns = ['Value', 'observedAverage', 'fittedAverage', 'Category', 'dataset']
        # Format numbers
        combined_data['observedAverage'] = [float('%s' % float('%.3g' % x)) for x in combined_data['observedAverage']]
        combined_data['fittedAverage'] = [float('%s' % float('%.3g' % x)) for x in combined_data['fittedAverage']]
        combined_data['Value'] = [float('%s' % float('%.3g' % x)) for x in combined_data['Value']]
        
        logger.debug('Data combined and formatted successfully.')

        return combined_data

        
    def get_lift_chart(self, nb_bins, train_set, test_set):
        """
        Calculates and returns the lift chart data for the model on the training set,
        divided into the specified number of bins.

        Args:
            nb_bins (int): The number of bins to divide the data into for the lift chart.

        Returns:
            pd.DataFrame: The aggregated lift chart data with observed and predicted metrics.
        """
        logger.debug(f'Starting to generate lift chart with {nb_bins} bins.')
        logger.debug(f'Starting to generate lift chart with train set length{len(train_set)} .')
        logger.debug(f'Starting to generate lift chart with test set length{len(test_set)} .')
        
        # Process training set
        lift_chart_data = self._process_set(
            train_set, 
            nb_bins, 
            'train'
        )
        
        # Process test set
        test_lift_chart_data = self._process_set(
            test_set, 
            nb_bins, 
            'test'
        )
        
        combined_lift_chart_data = self._combine_and_format_data(lift_chart_data, test_lift_chart_data)
        
        return combined_lift_chart_data