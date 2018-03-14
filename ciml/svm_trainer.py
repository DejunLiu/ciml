# Copyright 2018 IBM Corp.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import os

import numpy as np
import tensorflow as tf

tf.logging.set_verbosity(tf.logging.INFO)


class SVMTrainer(object):
    def __init__(self, examples, example_ids, labels, classes,
                 dataset_name='dataset', force_gpu=False):
        # Define feature names including the original CSV column name
        self.feature_columns = []
        for n in range(len(labels)):
            feature_data = examples[:, n]
            mean_fd = np.mean(feature_data)
            max_min_fd = np.max(feature_data) - np.min(feature_data)
            self.feature_columns.append(
                tf.contrib.layers.real_valued_column(
                    labels[n], normalizer=lambda x: (x - mean_fd) / max_min_fd))
        self.example_ids = example_ids
        self.examples = examples
        self.classes = classes
        self.force_gpu = force_gpu
        model_data_folder = os.sep.join([
            os.path.dirname(os.path.realpath(__file__)), os.pardir, 'data',
            dataset_name, 'model'])
        os.makedirs(model_data_folder, exist_ok=True)
        self.estimator = tf.contrib.learn.SVM(
            feature_columns=self.feature_columns,
            example_id_column='example_id',
            model_dir=model_data_folder,
            feature_engineering_fn=self.feature_engineering_fn)

    def input_fn(self):
        num_features = len(self.feature_columns)
        # Dict comprehension to build a dict of features
        # I suppose numpy might be able to do this more efficiently
        _features = {
            self.feature_columns[n].column_name:
                tf.constant(self.examples[:, n])
            for n in range(num_features)}
        _features['example_id'] = tf.constant(self.example_ids)
        print("Done preparing input data")
        return _features, tf.constant(self.classes)

    def feature_engineering_fn(self, features, labels):
        # Further data normalization may happen here
        print("Built engineered data")
        return features, labels

    def train(self, steps=30):
        if self.force_gpu:
            with tf.device('/device:GPU:0'):
                self.estimator.fit(input_fn=self.input_fn, steps=steps)
                train_loss = self.estimator.evaluate(input_fn=self.input_fn,
                                                     steps=1)
        else:
            self.estimator.fit(input_fn=self.input_fn, steps=steps)
            train_loss = self.estimator.evaluate(input_fn=self.input_fn,
                                                 steps=1)
        print('Training loss %r' % train_loss)
