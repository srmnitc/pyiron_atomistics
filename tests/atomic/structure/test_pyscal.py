# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.

import unittest
import numpy as np
import pyscal.core as pc
from pyiron_atomistics.atomistics.structure.atoms import Atoms, CrystalStructure
from ase.build import bulk
from pyiron_atomistics.atomistics.structure.atoms import ase_to_pyiron
import pyiron_atomistics.atomistics.structure.pyscal as pas
from pyiron_atomistics._tests import TestWithCleanProject


class Testpyscal(TestWithCleanProject):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.structure = cls.project.create.structure.bulk('Al', a=4, cubic=True).repeat(4)

    def test_attributes(self):
        self.assertIsInstance(self.structure, Atoms)

    def test_simple_system(self):
        """
        Test a simple ase to pyscal conversion
        """
        sysp = pc.System()
        sysp.read_inputfile(self.structure, format="ase")
        self.assertEqual(len(sysp.atoms), 256)

    def test_steinhardt_parameters_returns(self):
        self.assertEqual(2, len(pas.get_steinhardt_parameter_structure(self.structure)),
                         msg='Expected default return value to be a tuple of qs and cluster indices.')
        self.assertIsInstance(pas.get_steinhardt_parameter_structure(self.structure, n_clusters=None), np.ndarray,
                              msg='Expected just the qs when no clustering is used.')

    def test_steinhardt_parameters_qs(self):
        """
        Test the calculation of Steinhardts parameters
        """
        perfect_vals = [0.00, 0.00, 0.190, 0.00, 0.575, 0.00, 0.404, 0.00,
                        0.013, 0.00, 0.600]

        qtest = np.random.randint(2, 13, size=2)

        qs, _ = pas.get_steinhardt_parameter_structure(self.structure, cutoff=0, n_clusters=2, q=qtest)
        for c, q in enumerate(qs):
            self.assertLess(np.abs(np.mean(q) - perfect_vals[qtest[c]-2]), 1E-3)

    def test_steinhardt_parameters_clustering(self):
        noisy_structure = self.structure.copy()
        noisy_structure.positions += 0.5 * np.random.rand(*noisy_structure.positions.shape)
        n_clusters = 3
        _, inds = pas.get_steinhardt_parameter_structure(noisy_structure, n_clusters=n_clusters)
        self.assertEqual(n_clusters, len(np.unique(inds)), msg='Expected to find one label for each cluster.')

    def test_centrosymmetry(self):
        csm = pas.analyse_centro_symmetry(self.structure, num_neighbors=12)
        self.assertLess(np.mean(csm), 1E-5)

    def test_cna(self):
        cna = pas.analyse_cna_adaptive(self.structure)
        self.assertEqual(cna['fcc'], len(self.structure))

        rand = np.random.randint(0, len(self.structure))

        cna = pas.analyse_cna_adaptive(self.structure, mode="numeric")
        self.assertEqual(cna[rand], 1)

        cna = pas.analyse_cna_adaptive(self.structure, mode="str")
        self.assertEqual(cna[rand], "fcc")

    def test_volume(self):
        vols = pas.analyse_voronoi_volume(self.structure)
        self.assertLess(np.abs(np.mean(vols) - 16.0), 1E-3)


class Testpyscalatoms(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.al_fcc = ase_to_pyiron(bulk("Al", cubic=True))
        cls.fe_bcc = ase_to_pyiron(bulk("Fe", cubic=True))
        cls.ti_hcp = ase_to_pyiron(bulk("Ti", orthorhombic=True))
        cls.si_dia = ase_to_pyiron(bulk("Si", cubic=True))
        cls.al_fcc_4 = CrystalStructure(element="Al",
                                        bravais_basis="fcc",
                                        lattice_constants=4
                                        ).repeat(4)

    def test_steinhardt_parameters(self):
        """ Test the calculation of Steinhardts parameters using the Analyse class. """
        perfect_vals = [0.00, 0.00, 0.190, 0.00, 0.575, 0.00, 0.404, 0.00,
                        0.013, 0.00, 0.600]

        qtest = np.random.randint(2, 13, size=2)

        qs, _ = self.al_fcc_4.analyse.pyscal_steinhardt_parameter(cutoff=0, n_clusters=2, q=qtest)
        for c, q in enumerate(qs):
            self.assertLess(np.abs(np.mean(q) - perfect_vals[qtest[c]-2]), 1E-3)

    def test_analyse_pyscal_centro_symmetry(self):
        self.assertTrue(all([np.isclose(v, 0.0) for v in self.al_fcc.analyse.pyscal_centro_symmetry(num_neighbors=12)]))
        self.assertTrue(all([np.isclose(v, 0.0) for v in self.fe_bcc.analyse.pyscal_centro_symmetry(num_neighbors=8)]))
        self.assertTrue(all([np.isclose(v, 8.7025) for v in self.ti_hcp.analyse.pyscal_centro_symmetry(num_neighbors=12)]))
        self.assertTrue(all([np.isclose(v, 14.742449) for v in self.si_dia.analyse.pyscal_centro_symmetry(num_neighbors=4)]))
        self.assertEqual(len(self.al_fcc.analyse.pyscal_centro_symmetry()), len(self.al_fcc))
        self.assertEqual(len(self.fe_bcc.analyse.pyscal_centro_symmetry()), len(self.fe_bcc))
        self.assertEqual(len(self.ti_hcp.analyse.pyscal_centro_symmetry()), len(self.ti_hcp))
        self.assertEqual(len(self.si_dia.analyse.pyscal_centro_symmetry()), len(self.si_dia))

    def test_analyse_pyscal_voronoi_volume(self):
        self.assertAlmostEqual(np.mean(self.al_fcc.analyse.pyscal_voronoi_volume()), 16.60753125)
        self.assertAlmostEqual(np.mean(self.fe_bcc.analyse.pyscal_voronoi_volume()), 11.8199515)
        self.assertAlmostEqual(np.mean(self.ti_hcp.analyse.pyscal_voronoi_volume()), 17.65294557)
        self.assertAlmostEqual(np.mean(self.si_dia.analyse.pyscal_voronoi_volume()), 20.01287587)
        self.assertEqual(len(self.al_fcc.analyse.pyscal_voronoi_volume()), len(self.al_fcc))
        self.assertEqual(len(self.fe_bcc.analyse.pyscal_voronoi_volume()), len(self.fe_bcc))
        self.assertEqual(len(self.ti_hcp.analyse.pyscal_voronoi_volume()), len(self.ti_hcp))
        self.assertEqual(len(self.si_dia.analyse.pyscal_voronoi_volume()), len(self.si_dia))

    def test_analyse_pyscal_cna_adaptive(self):
        pyscal_keys = [
            'others', 'fcc', 'hcp', 'bcc', 'ico',
        ]
        ovito_keys = [
            'CommonNeighborAnalysis.counts.OTHER',
            'CommonNeighborAnalysis.counts.FCC',
            'CommonNeighborAnalysis.counts.HCP',
            'CommonNeighborAnalysis.counts.BCC',
             'CommonNeighborAnalysis.counts.ICO'
        ]
        res_dict_total = self.al_fcc.analyse.pyscal_cna_adaptive(mode="total", ovito_compatibility=False)
        self.assertEqual(sum([k in res_dict_total.keys() for k in pyscal_keys]), len(pyscal_keys))
        self.assertEqual(res_dict_total[pyscal_keys[1]], len(self.al_fcc))
        res_dict_total = self.fe_bcc.analyse.pyscal_cna_adaptive(mode="total", ovito_compatibility=False)
        self.assertEqual(sum([k in res_dict_total.keys() for k in pyscal_keys]), len(pyscal_keys))
        self.assertEqual(res_dict_total[pyscal_keys[3]], len(self.fe_bcc))
        res_dict_total = self.ti_hcp.analyse.pyscal_cna_adaptive(mode="total", ovito_compatibility=False)
        self.assertEqual(sum([k in res_dict_total.keys() for k in pyscal_keys]), len(pyscal_keys))
        self.assertEqual(res_dict_total[pyscal_keys[2]], len(self.ti_hcp))
        res_dict_total = self.si_dia.analyse.pyscal_cna_adaptive(mode="total", ovito_compatibility=False)
        self.assertEqual(sum([k in res_dict_total.keys() for k in pyscal_keys]), len(pyscal_keys))
        self.assertEqual(res_dict_total[pyscal_keys[0]], len(self.si_dia))

        res_numeric = self.al_fcc.analyse.pyscal_cna_adaptive(mode="numeric", ovito_compatibility=False)
        self.assertEqual(len(res_numeric), len(self.al_fcc))
        self.assertTrue(all([v == 1 for v in res_numeric]))
        res_numeric = self.fe_bcc.analyse.pyscal_cna_adaptive(mode="numeric", ovito_compatibility=False)
        self.assertEqual(len(res_numeric), len(self.fe_bcc))
        self.assertTrue(all([v == 3 for v in res_numeric]))
        res_numeric = self.ti_hcp.analyse.pyscal_cna_adaptive(mode="numeric", ovito_compatibility=False)
        self.assertEqual(len(res_numeric), len(self.ti_hcp))
        self.assertTrue(all([v == 2 for v in res_numeric]))
        res_numeric = self.si_dia.analyse.pyscal_cna_adaptive(mode="numeric", ovito_compatibility=False)
        self.assertEqual(len(res_numeric), len(self.si_dia))
        self.assertTrue(all([v == 0 for v in res_numeric]))

        res_str = self.al_fcc.analyse.pyscal_cna_adaptive(mode="str", ovito_compatibility=False)
        self.assertEqual(len(res_str), len(self.al_fcc))
        self.assertTrue(all([v == 'fcc' for v in res_str]))
        res_str = self.fe_bcc.analyse.pyscal_cna_adaptive(mode="str", ovito_compatibility=False)
        self.assertEqual(len(res_str), len(self.fe_bcc))
        self.assertTrue(all([v == 'bcc' for v in res_str]))
        res_str = self.ti_hcp.analyse.pyscal_cna_adaptive(mode="str", ovito_compatibility=False)
        self.assertEqual(len(res_str), len(self.ti_hcp))
        self.assertTrue(all([v == 'hcp' for v in res_str]))
        res_str = self.si_dia.analyse.pyscal_cna_adaptive(mode="str", ovito_compatibility=False)
        self.assertEqual(len(res_str), len(self.si_dia))
        self.assertTrue(all([v == 'others' for v in res_str]))

        res_dict_total = self.al_fcc.analyse.pyscal_cna_adaptive(mode="total", ovito_compatibility=True)
        self.assertEqual(sum([k in res_dict_total.keys() for k in ovito_keys]), len(ovito_keys))
        self.assertEqual(res_dict_total[ovito_keys[1]], len(self.al_fcc))
        res_dict_total = self.fe_bcc.analyse.pyscal_cna_adaptive(mode="total", ovito_compatibility=True)
        self.assertEqual(sum([k in res_dict_total.keys() for k in ovito_keys]), len(ovito_keys))
        self.assertEqual(res_dict_total[ovito_keys[3]], len(self.fe_bcc))
        res_dict_total = self.ti_hcp.analyse.pyscal_cna_adaptive(mode="total", ovito_compatibility=True)
        self.assertEqual(sum([k in res_dict_total.keys() for k in ovito_keys]), len(ovito_keys))
        self.assertEqual(res_dict_total[ovito_keys[2]], len(self.ti_hcp))
        res_dict_total = self.si_dia.analyse.pyscal_cna_adaptive(mode="total", ovito_compatibility=True)
        self.assertEqual(sum([k in res_dict_total.keys() for k in ovito_keys]), len(ovito_keys))
        self.assertEqual(res_dict_total[ovito_keys[0]], len(self.si_dia))

        res_numeric = self.al_fcc.analyse.pyscal_cna_adaptive(mode="numeric", ovito_compatibility=True)
        self.assertEqual(len(res_numeric), len(self.al_fcc))
        self.assertTrue(all([v == 1 for v in res_numeric]))
        res_numeric = self.fe_bcc.analyse.pyscal_cna_adaptive(mode="numeric", ovito_compatibility=True)
        self.assertEqual(len(res_numeric), len(self.fe_bcc))
        self.assertTrue(all([v == 3 for v in res_numeric]))
        res_numeric = self.ti_hcp.analyse.pyscal_cna_adaptive(mode="numeric", ovito_compatibility=True)
        self.assertEqual(len(res_numeric), len(self.ti_hcp))
        self.assertTrue(all([v == 2 for v in res_numeric]))
        res_numeric = self.si_dia.analyse.pyscal_cna_adaptive(mode="numeric", ovito_compatibility=True)
        self.assertEqual(len(res_numeric), len(self.si_dia))
        self.assertTrue(all([v == 0 for v in res_numeric]))

        res_str = self.al_fcc.analyse.pyscal_cna_adaptive(mode="str", ovito_compatibility=True)
        self.assertEqual(len(res_str), len(self.al_fcc))
        self.assertTrue(all([v == 'FCC' for v in res_str]))
        res_str = self.fe_bcc.analyse.pyscal_cna_adaptive(mode="str", ovito_compatibility=True)
        self.assertEqual(len(res_str), len(self.fe_bcc))
        self.assertTrue(all([v == 'BCC' for v in res_str]))
        res_str = self.ti_hcp.analyse.pyscal_cna_adaptive(mode="str", ovito_compatibility=True)
        self.assertEqual(len(res_str), len(self.ti_hcp))
        self.assertTrue(all([v == 'HCP' for v in res_str]))
        res_str = self.si_dia.analyse.pyscal_cna_adaptive(mode="str", ovito_compatibility=True)
        self.assertEqual(len(res_str), len(self.si_dia))
        self.assertTrue(all([v == 'Other' for v in res_str]))

    def test_analyse_pyscal_diamond_structure(self):
        pyscal_keys = [
            'others', 'fcc', 'hcp', 'bcc', 'ico',
            'cubic diamond', 'cubic diamond 1NN', 'cubic diamond 2NN',
            'hex diamond', 'hex diamond 1NN', 'hex diamond 2NN'
        ]
        ovito_keys = [
            'IdentifyDiamond.counts.CUBIC_DIAMOND',
            'IdentifyDiamond.counts.CUBIC_DIAMOND_FIRST_NEIGHBOR',
            'IdentifyDiamond.counts.CUBIC_DIAMOND_SECOND_NEIGHBOR',
            'IdentifyDiamond.counts.HEX_DIAMOND',
            'IdentifyDiamond.counts.HEX_DIAMOND_FIRST_NEIGHBOR',
            'IdentifyDiamond.counts.HEX_DIAMOND_SECOND_NEIGHBOR',
            'IdentifyDiamond.counts.OTHER'
        ]
        res_dict_total = self.al_fcc.analyse.pyscal_diamond_structure(mode="total", ovito_compatibility=False)
        self.assertEqual(sum([k in res_dict_total.keys() for k in pyscal_keys]), len(pyscal_keys))
        self.assertEqual(res_dict_total[pyscal_keys[0]], len(self.al_fcc))
        res_dict_total = self.fe_bcc.analyse.pyscal_diamond_structure(mode="total", ovito_compatibility=False)
        self.assertEqual(sum([k in res_dict_total.keys() for k in pyscal_keys]), len(pyscal_keys))
        self.assertEqual(res_dict_total[pyscal_keys[0]], len(self.fe_bcc))
        res_dict_total = self.ti_hcp.analyse.pyscal_diamond_structure(mode="total", ovito_compatibility=False)
        self.assertEqual(sum([k in res_dict_total.keys() for k in pyscal_keys]), len(pyscal_keys))
        self.assertEqual(res_dict_total[pyscal_keys[0]], len(self.ti_hcp))
        res_dict_total = self.si_dia.analyse.pyscal_diamond_structure(mode="total", ovito_compatibility=False)
        self.assertEqual(sum([k in res_dict_total.keys() for k in pyscal_keys]), len(pyscal_keys))
        self.assertEqual(res_dict_total[pyscal_keys[5]], len(self.si_dia))

        res_numeric = self.al_fcc.analyse.pyscal_diamond_structure(mode="numeric", ovito_compatibility=False)
        self.assertEqual(len(res_numeric), len(self.al_fcc))
        self.assertTrue(all([v == 0 for v in res_numeric]))
        res_numeric = self.fe_bcc.analyse.pyscal_diamond_structure(mode="numeric", ovito_compatibility=False)
        self.assertEqual(len(res_numeric), len(self.fe_bcc))
        self.assertTrue(all([v == 0 for v in res_numeric]))
        res_numeric = self.ti_hcp.analyse.pyscal_diamond_structure(mode="numeric", ovito_compatibility=False)
        self.assertEqual(len(res_numeric), len(self.ti_hcp))
        self.assertTrue(all([v == 0 for v in res_numeric]))
        res_numeric = self.si_dia.analyse.pyscal_diamond_structure(mode="numeric", ovito_compatibility=False)
        self.assertEqual(len(res_numeric), len(self.si_dia))
        self.assertTrue(all([v == 5 for v in res_numeric]))

        res_str = self.al_fcc.analyse.pyscal_diamond_structure(mode="str", ovito_compatibility=False)
        self.assertEqual(len(res_str), len(self.al_fcc))
        self.assertTrue(all([v == 'others' for v in res_str]))
        res_str = self.fe_bcc.analyse.pyscal_diamond_structure(mode="str", ovito_compatibility=False)
        self.assertEqual(len(res_str), len(self.fe_bcc))
        self.assertTrue(all([v == 'others' for v in res_str]))
        res_str = self.ti_hcp.analyse.pyscal_diamond_structure(mode="str", ovito_compatibility=False)
        self.assertEqual(len(res_str), len(self.ti_hcp))
        self.assertTrue(all([v == 'others' for v in res_str]))
        res_str = self.si_dia.analyse.pyscal_diamond_structure(mode="str", ovito_compatibility=False)
        self.assertEqual(len(res_str), len(self.si_dia))
        self.assertTrue(all([v == 'cubic diamond' for v in res_str]))

        res_dict_total = self.al_fcc.analyse.pyscal_diamond_structure(mode="total", ovito_compatibility=True)
        self.assertEqual(sum([k in res_dict_total.keys() for k in ovito_keys]), len(ovito_keys))
        self.assertEqual(res_dict_total[ovito_keys[6]], len(self.al_fcc))
        res_dict_total = self.fe_bcc.analyse.pyscal_diamond_structure(mode="total", ovito_compatibility=True)
        self.assertEqual(sum([k in res_dict_total.keys() for k in ovito_keys]), len(ovito_keys))
        self.assertEqual(res_dict_total[ovito_keys[6]], len(self.fe_bcc))
        res_dict_total = self.ti_hcp.analyse.pyscal_diamond_structure(mode="total", ovito_compatibility=True)
        self.assertEqual(sum([k in res_dict_total.keys() for k in ovito_keys]), len(ovito_keys))
        self.assertEqual(res_dict_total[ovito_keys[6]], len(self.ti_hcp))
        res_dict_total = self.si_dia.analyse.pyscal_diamond_structure(mode="total", ovito_compatibility=True)
        self.assertEqual(sum([k in res_dict_total.keys() for k in ovito_keys]), len(ovito_keys))
        self.assertEqual(res_dict_total[ovito_keys[0]], len(self.si_dia))

        res_numeric = self.al_fcc.analyse.pyscal_diamond_structure(mode="numeric", ovito_compatibility=True)
        self.assertEqual(len(res_numeric), len(self.al_fcc))
        self.assertTrue(all([v == 6 for v in res_numeric]))
        res_numeric = self.fe_bcc.analyse.pyscal_diamond_structure(mode="numeric", ovito_compatibility=True)
        self.assertEqual(len(res_numeric), len(self.fe_bcc))
        self.assertTrue(all([v == 6 for v in res_numeric]))
        res_numeric = self.ti_hcp.analyse.pyscal_diamond_structure(mode="numeric", ovito_compatibility=True)
        self.assertEqual(len(res_numeric), len(self.ti_hcp))
        self.assertTrue(all([v == 6 for v in res_numeric]))
        res_numeric = self.si_dia.analyse.pyscal_diamond_structure(mode="numeric", ovito_compatibility=True)
        self.assertEqual(len(res_numeric), len(self.si_dia))
        self.assertTrue(all([v == 0 for v in res_numeric]))

        res_str = self.al_fcc.analyse.pyscal_diamond_structure(mode="str", ovito_compatibility=True)
        self.assertEqual(len(res_str), len(self.al_fcc))
        self.assertTrue(all([v == 'Other' for v in res_str]))
        res_str = self.fe_bcc.analyse.pyscal_diamond_structure(mode="str", ovito_compatibility=True)
        self.assertEqual(len(res_str), len(self.fe_bcc))
        self.assertTrue(all([v == 'Other' for v in res_str]))
        res_str = self.ti_hcp.analyse.pyscal_diamond_structure(mode="str", ovito_compatibility=True)
        self.assertEqual(len(res_str), len(self.ti_hcp))
        self.assertTrue(all([v == 'Other' for v in res_str]))
        res_str = self.si_dia.analyse.pyscal_diamond_structure(mode="str", ovito_compatibility=True)
        self.assertEqual(len(res_str), len(self.si_dia))
        self.assertTrue(all([v == 'Cubic diamond' for v in res_str]))


if __name__ == "__main__":
    unittest.main()
