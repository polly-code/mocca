# flake8: noqa


# All following functions should be put in other class
def check_database(self, component_database, abs_threshold=100,
                   rel_threshold=0.01, similarity_threshold=0.9):
    """
    Computes if the peak matches one already seen in the database, based
    on retention time and UV-Vis spectra.

    Parameters
    ----------
    component_database : micdrop.ComponentDatabase
        A component database containing all seen components.

    abs_threshold : numeric
        The absolute number of timepoints that the retention time is allowed to
        be off by. Default is 100.

    rel_threshold : numeric
        The relative fraction of timepoints that the retention time is allowed to
        be off by. Default is 0.01.

    similarity_threshold : numeric
        The correlation needed between spectra to match a component in the
        component database. Default is 0.9

    Returns
    --------
    str : The name of the closest matching Component if there was a match,
    or "Unknown" if there was no match.
    """
    matches = []
    for component in component_database:
        similarity = np.corrcoef(component.spectra,
                                 self.dataset.data[:, self.maximum])[1, 0]
        distance_to_max = abs(component.maximum - self.maximum)
        if distance_to_max < abs_threshold + rel_threshold * component.maximum and \
                similarity > similarity_threshold:
            matches.append({'compound_id': component.compound_id, 'similarity': similarity})
        # sort in decreasing order, based on similarity of spectra
        matches.sort(key=lambda x: -x['similarity'])

    if len(matches) == 0:
        logging.warning("Warning: check_database() found no matches for peak {}, setting compound_id as Unknown".format(self.idx))
        return "Unknown"

    if len(matches) > 1:
        logging.warning("Warning: check_database() found multiple matches for peak {}, the full list is {}".format(self.idx, matches))

    return matches[0]['compound_id']

def set_compound_id(self, component_database, abs_threshold=100,
                    rel_threshold=0.01, similarity_threshold=0.9):
    """
    Checks if the peak is in the database, and if so, sets self.compound_id.
    See check_database().

    Modifies
    --------
    self.compound_id
        If a match is found, then the peak's compound_id attribute is set.
    """
    if self.pure is None or not self.pure:
        logging.warning("Warning: Running set_compound_id() on impure \
                        peak {}.".format(self.idx))

    self.compound_id = self.check_database(component_database=component_database,
                                           abs_threshold=abs_threshold,
                                           rel_threshold=rel_threshold,
                                           similarity_threshold=similarity_threshold) 

def quantify_peak(self, quantification_database):
    """
    Computes the concentration of the compound in this peak.

    The attributes self.integral and self.compound_id must be set beforehand
    (through functions self.integrate_peak() and self.check_database())
    in order to quantify.

    Parameters
    ----------
    quantification_database : micdrop.QuantificationDatabase
        A quantification database containing all seen components.

    Raises Exception if the attributes self.integral or self.compound_id are
    not set. Prints a text warning if self.pure is not set.

    Modifies
    --------
    self.concentration : sets concentration to that predicted by integral
    """
    if self.integral is None or self.compound_id is None:
        raise Exception("Must set peak integral and compound_id before \
                        attempting to quantify!")

    if self.pure is None or not self.pure:
        logging.warning("Warning: Running quantify_peak() on impure peak \
                        {}.".format(self.idx))

    self.concentration = quantification_database.quantify_peak(self.integral,
                                                               self.compound_id)
    
# PEAK CHECK DATABASE TESTS

def test_check_database_1():
    # normal functioning database
    peak_1 = Peak(left=130, right=170, maximum=150, dataset=test_data_1)
    peak_2 = Peak(left=280, right=330, maximum=300, dataset=test_data_1)
    component_database = ComponentDatabase()
    component_database.add_peak(peak_1, 'Component 1')
    component_database.add_peak(peak_2, 'Component 2')

    # minor variations in peak location
    test_peak_1 = Peak(left=120, right=165, maximum=152, dataset=test_data_7)
    test_peak_2 = Peak(left=270, right=325, maximum=298, dataset=test_data_7)

    test_peaks = [test_peak_1, test_peak_2]
    for peak in test_peaks:
        peak.process_peak(absorbance_threshold=0.1, detector_limit=10)
        peak.set_compound_id(component_database)

    assert test_peak_1.compound_id == 'Component 1'
    assert test_peak_2.compound_id == 'Component 2'


def test_check_database_2():
    # add different peaks at same retention time
    # similar peak at same time point
    peak_1 = Peak(left=130, right=170, maximum=150, dataset=test_data_8)
    peak_2 = Peak(left=130, right=170, maximum=150, dataset=test_data_1)
    component_database = ComponentDatabase()
    component_database.add_peak(peak_1, 'Component 1')
    component_database.add_peak(peak_2, 'Component 2')

    test_peak_1 = Peak(left=120, right=165,
                       maximum=152, dataset=test_data_7)  # peak 2
    test_peak_2 = Peak(left=270, right=325,
                       maximum=298, dataset=test_data_7)  # nothing

    test_peaks = [test_peak_1, test_peak_2]
    for peak in test_peaks:
        peak.process_peak(absorbance_threshold=0.1, detector_limit=10)
        peak.set_compound_id(component_database, similarity_threshold=0.85)
        # custom similarity threshold to actually cause two matches

    assert test_peak_1.check_database(component_database) == 'Component 2'
    assert test_peak_2.check_database(component_database) == 'Unknown'
    assert test_peak_1.compound_id == 'Component 2'
    assert test_peak_2.compound_id == 'Unknown'