import joblib
import numpy as np
import tensorflow as tf
from pooch import retrieve

from alfabet import _model_files_baseurl
from alfabet.drawing import draw_bde
from alfabet.prediction import preprocessor, model, bde_dft

embedding_model = tf.keras.Model(model.inputs, [model.layers[31].input])

nbrs_pipe = joblib.load(retrieve(
    _model_files_baseurl + 'bond_embedding_nbrs.p.z',
    known_hash='sha256:187df1e88a5fafc1e83436f86ea0374df678e856f2c17506bc730de1996a47b1'))


def pipe_kneighbors(pipe, X):
    Xt = pipe.steps[0][-1].transform(X)
    return pipe.steps[-1][-1].kneighbors(Xt)


def find_neighbor_bonds(smiles, bond_index, draw=False):
    inputs = preprocessor.construct_feature_matrices(smiles, train=False)
    embeddings = embedding_model({key: tf.constant(np.expand_dims(val, 0), name=val) for key, val in inputs.items()})
    distances, indices = pipe_kneighbors(nbrs_pipe, embeddings[:, bond_index, :])

    neighbor_df = bde_dft.dropna().iloc[indices.flatten()]
    neighbor_df['distance'] = distances.flatten()
    neighbor_df = neighbor_df.drop_duplicates(
        ['molecule', 'fragment1', 'fragment2']).sort_values('distance')

    if draw:
        neighbor_df['svg'] = neighbor_df.apply(
            lambda x: draw_bde(x.molecule, x.bond_index), 1)

    return neighbor_df
