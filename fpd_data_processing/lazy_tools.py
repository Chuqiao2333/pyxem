from tqdm import tqdm
import numpy as np


def _get_dask_chunk_slice_list(dask_array):
    """Generate a list of NumPy slice objects for a dask array

    Parameters
    ----------
    dask_array : dask array

    Returns
    -------
    slice_list : list of NumPy slice objects

    Examples
    --------
    >>> import dask.array as da
    >>> data = da.random.random((64, 64, 100, 100), chunks=(8, 8, 100, 100))
    >>> import fpd_data_processing.lazy_tools as lt
    >>> slice_list = lt._get_dask_chunk_slice_list(data)

    """
    chunk_list_dim = dask_array.shape
    if (len(chunk_list_dim) == 2) or (len(chunk_list_dim) > 4):
        raise NotImplementedError(
                "dask_array must have either 3 or 4 dimensions")
    temp_slice_list = []
    for chunk_list in dask_array.chunks[:-2]:
        temp_slice_dim = []
        current_v = 0
        for chunk in chunk_list:
            temp_slice_dim.append((current_v, current_v + chunk))
            current_v += chunk
        temp_slice_list.append(temp_slice_dim)

    slice_list = []
    if len(temp_slice_list) == 1:
        for slice_t in temp_slice_list[0]:
            temp_slice = np.s_[slice_t[0]:slice_t[1], :, :]
            slice_list.append(temp_slice)
    elif len(temp_slice_list) == 2:
        for slice_t0 in temp_slice_list[0]:
            for slice_t1 in temp_slice_list[1]:
                    temp_slice = np.s_[
                            slice_t0[0]:slice_t0[1],
                            slice_t1[0]:slice_t1[1], :, :]
                    slice_list.append(temp_slice)
    return slice_list


def _calculate_function_on_dask_array(
        dask_array, function, func_args=None, return_sig_size=1,
        show_progressbar=True):
    """Apply a function to a dask array, immediately returning the results.

    Parameters
    ----------
    dask_array : dask array
    function : function
    func_args : dict
    return_sig_size : int
        Default 1
    show_progressbar : bool
        Default True

    Return
    ------
    return_data : NumPy array

    Examples
    --------
    >>> import dask.array as da
    >>> dask_data = da.random.random(
    ...     (64, 64, 100, 100), chunks=(8, 8, 100, 100))
    >>> import fpd_data_processing.pixelated_stem_tools as pst
    >>> import fpd_data_processing.lazy_tools as lt
    >>> out_data = lt._calculate_function_on_dask_array(
    ...     dask_data, pst._center_of_mass_single_frame,
    ...     return_sig_size=2, show_progressbar=False)

    """
    if (len(dask_array.shape) == 2) or (len(dask_array.shape) > 4):
        raise NotImplementedError(
                "dask_array must have either 3 or 4 dimensions")
    if func_args is None:
        func_args = {}
    if return_sig_size == 1:
        return_data = np.zeros((*dask_array.shape[:-2], ))
    else:
        return_data = np.zeros((*dask_array.shape[:-2], return_sig_size))
    slice_list = _get_dask_chunk_slice_list(dask_array)
    for slice_chunk in tqdm(slice_list):
        data_slice = dask_array[slice_chunk]
        data_slice = data_slice.compute()
        im_slice_list = []
        data_slice_shape = data_slice.shape[:-2]
        if len(data_slice_shape) == 1:
            for im_slice0 in range(data_slice_shape[0]):
                im_slice_list.append(np.s_[im_slice0, :, :])
            for im_slice in im_slice_list:
                im = data_slice[im_slice]
                i = slice_chunk.start + im_slice[0]
                out_data = function(im, **func_args)
                if return_sig_size == 1:
                    return_data[i] = out_data
                else:
                    return_data[i, :] = out_data
        elif len(data_slice_shape) == 2:
            for im_slice0 in range(data_slice_shape[0]):
                for im_slice1 in range(data_slice_shape[1]):
                    im_slice_list.append(np.s_[im_slice0, im_slice1, :, :])
            for im_slice in im_slice_list:
                im = data_slice[im_slice]
                i_x = slice_chunk[0].start + im_slice[0]
                i_y = slice_chunk[1].start + im_slice[1]
                out_data = function(im, **func_args)
                if return_sig_size == 1:
                    return_data[i_x, i_y] = out_data
                else:
                    return_data[i_x, i_y, :] = out_data
    return return_data
