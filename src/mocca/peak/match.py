#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec  1 12:06:57 2021

@author: haascp
"""
import numpy as np

from mocca.peak.models import PreprocessedPeak
from mocca.peak.utils import average_peak_spectrum


def get_spectrum_correl_coef(peak, component):
    """
    Returns the correlation coefficient of the average peak spectrum and the
    spectrum of the component.
    """
    peak_spectrum = average_peak_spectrum(peak)
    return np.corrcoef(peak_spectrum, component.spectrum)[1, 0]


def get_relative_distance(peak, component):
    """
    Returns the distance of two peak maxima relative to the length of the time
    vector.
    """
    distance = abs(peak.maximum - component.maximum)
    return distance / len(peak.dataset.time)


def get_similarity_dicts(peak, component_db):
    """
    Returns a sorted list of dictionaries. For each component in the given
    database, similarity values to the given peak are stored.
    """
    simil_by_comp = []
    for component in component_db:
        dic = {}
        dic['compound_id'] = component.compound_id
        dic['spectrum_correl_coef'] = get_spectrum_correl_coef(peak, component)
        dic['distance'] = abs(peak.maximum - component.maximum)
        dic['relative_distance'] = get_relative_distance(peak, component)
        simil_by_comp.append(dic)
    simil_by_comp = sorted(simil_by_comp, reverse=True,
                           key=lambda dic: dic['spectrum_correl_coef'])
    return simil_by_comp


def get_filtered_similarity_dicts(peak, component_db, spectrum_correl_coef_thresh,
                                  relative_distance_thresh, print_out):
    """
    Filters the list of similarity dictionaries with regard to the given thresholds.
    Return possible matches which have a spectral correlation coefficient higher
    than the given threshold and a relative distance between the peak maxima
    lower than the given threshold.
    """
    similarity_dict = get_similarity_dicts(peak, component_db)
    if print_out:
        print(similarity_dict)
    for d in similarity_dict:
        print(d['spectrum_correl_coef'] >= spectrum_correl_coef_thresh)
        print(d['relative_distance'] <= spectrum_correl_coef_thresh)
    matches = [d for d in similarity_dict if ((d['spectrum_correl_coef'] >=
                                              spectrum_correl_coef_thresh) and
                                              (d['relative_distance'] <=
                                              relative_distance_thresh))]
    if print_out:
        print(matches)
    return matches


def match_peak(integrated_peak, component_db, spectrum_correl_coef_thresh,
               relative_distance_thresh, print_similarity_dicts):
    """
    Routine to assign possible matches to a returned preprocessed peak.
    """
    matches = get_filtered_similarity_dicts(integrated_peak, component_db,
                                            spectrum_correl_coef_thresh,
                                            relative_distance_thresh,
                                            print_similarity_dicts)
    return PreprocessedPeak(left=integrated_peak.left,
                            right=integrated_peak.right,
                            maximum=integrated_peak.maximum,
                            dataset=integrated_peak.dataset,
                            idx=integrated_peak.idx,
                            saturation=integrated_peak.saturation,
                            pure=integrated_peak.pure,
                            integral=integrated_peak.integral,
                            matches=matches)
