import sys

sys.path.append("src")

import unittest

from model import logica_pension


class TestPension(unittest.TestCase):

    def test_normal_1(self):
        datos = logica_pension.DatosPension(
            ibc_ultimos_10=9_800_000,
            ibc_toda_vida=10_000_000,
            salario_minimo_legal=2_000_000,
            semanas_cotizadas=1300,
            edad=65,
            sexo="M"
        )

        pension_esperada = 6_300_000.00

        resultado = logica_pension.calcular_pension(datos)
        self.assertAlmostEqual(pension_esperada,resultado.pension,2)

    def test_normal_2(self):
        datos = logica_pension.DatosPension(
            ibc_ultimos_10=1_950_000,
            ibc_toda_vida=2_000_000,
            salario_minimo_legal=2_000_000,
            semanas_cotizadas=1300,
            edad=60,
            sexo="F"
        )

        pension_esperada = 2_000_000.00

        resultado = logica_pension.calcular_pension(datos)
        self.assertAlmostEqual(pension_esperada,resultado.pension,2)

    def test_normal_3(self):
        datos = logica_pension.DatosPension(
            ibc_ultimos_10=3_700_000,
            ibc_toda_vida=3_900_000,
            salario_minimo_legal=2_000_000,
            semanas_cotizadas=1500,
            edad=63,
            sexo="M"
        )

        pension_esperada = 2_750_475.00

        resultado = logica_pension.calcular_pension(datos)
        self.assertAlmostEqual( pension_esperada,resultado.pension,2)

    def test_normal_4(self):
        datos = logica_pension.DatosPension(
            ibc_ultimos_10=15_200_000,
            ibc_toda_vida=15_600_000,
            salario_minimo_legal=2_000_000,
            semanas_cotizadas=1800,
            edad=64,
            sexo="M"
        )

        pension_esperada = 11_949_600.00

        resultado = logica_pension.calcular_pension(datos)
        self.assertAlmostEqual(pension_esperada,resultado.pension,2)

    def test_normal_5(self):
        datos = logica_pension.DatosPension(
            ibc_ultimos_10=2_500_000,
            ibc_toda_vida=2_600_000,
            salario_minimo_legal=2_000_000,
            semanas_cotizadas=2500,
            edad=65,
            sexo="F"
        )

        pension_esperada = 2_080_000.00

        resultado = logica_pension.calcular_pension(datos)
        self.assertAlmostEqual( pension_esperada,resultado.pension,2)

    def test_normal_6(self):
        datos = logica_pension.DatosPension(
            ibc_ultimos_10=25_000_000,
            ibc_toda_vida=26_000_000,
            salario_minimo_legal=2_000_000,
            semanas_cotizadas=1300,
            edad=62,
            sexo="M"
        )

        pension_esperada = 15_340_000.00

        resultado = logica_pension.calcular_pension(datos)

        self.assertAlmostEqual(pension_esperada,resultado.pension,2)

    def test_semanas_insuficientes(self):
        datos = logica_pension.DatosPension(
            ibc_ultimos_10=4_800_000,
            ibc_toda_vida=5_000_000,
            salario_minimo_legal=2_000_000,
            semanas_cotizadas=1200,
            edad=65,
            sexo="M"
        )

        with self.assertRaises(logica_pension.SemanasInsuficientes):
            logica_pension.calcular_pension(datos)

    def test_ibl_0(self):
        datos = logica_pension.DatosPension(
            ibc_ultimos_10=0,
            ibc_toda_vida=0,
            salario_minimo_legal=2_000_000,
            semanas_cotizadas=1300,
            edad=60,
            sexo="F"
        )

        with self.assertRaises(logica_pension.IblCero):
            logica_pension.calcular_pension(datos)

    def test_smlmv_0(self):
        datos = logica_pension.DatosPension(
            ibc_ultimos_10=4_800_000,
            ibc_toda_vida=5_000_000,
            salario_minimo_legal=0,
            semanas_cotizadas=1300,
            edad=62,
            sexo="M"
        )

        with self.assertRaises(logica_pension.SalarioMinimoLegalVigenteCero):
            logica_pension.calcular_pension(datos)

    def test_smlmv_negativo(self):
        datos = logica_pension.DatosPension(
            ibc_ultimos_10=4_800_000,
            ibc_toda_vida=5_000_000,
            salario_minimo_legal=-2_000_000,
            semanas_cotizadas=1300,
            edad=62,
            sexo="M"
        )

        with self.assertRaises(logica_pension.SalarioMinimoNegativo):
            logica_pension.calcular_pension(datos)

    def test_semanas_negativas(self):
        datos = logica_pension.DatosPension(
            ibc_ultimos_10=4_800_000,
            ibc_toda_vida=5_000_000,
            salario_minimo_legal=2_000_000,
            semanas_cotizadas=-100,
            edad=65,
            sexo="M"
        )

        with self.assertRaises(logica_pension.SemanasNegativas):
            logica_pension.calcular_pension(datos)

    def test_ibl_negativo(self):
        datos = logica_pension.DatosPension(
            ibc_ultimos_10=-2_900_000,
            ibc_toda_vida=-3_000_000,
            salario_minimo_legal=2_000_000,
            semanas_cotizadas=1300,
            edad=60,
            sexo="F"
        )

        with self.assertRaises(logica_pension.IblNegativo):
            logica_pension.calcular_pension(datos)

    def test_edad_insuficiente(self):
        datos = logica_pension.DatosPension(
            ibc_ultimos_10=4_800_000,
            ibc_toda_vida=5_000_000,
            salario_minimo_legal=2_000_000,
            semanas_cotizadas=1300,
            edad=45,
            sexo="F"
        )

        with self.assertRaises(logica_pension.EdadInsuficiente):
            logica_pension.calcular_pension(datos)

    # =========================
    # CASOS EXCEPCIONALES
    # =========================

    def test_excepcional_edad_limite_mujer(self):
        datos = logica_pension.DatosPension(
            ibc_ultimos_10=1_950_000,
            ibc_toda_vida=2_000_000,
            salario_minimo_legal=2_000_000,
            semanas_cotizadas=1300,
            edad=57,
            sexo="F"
        )

        pension_esperada = 2_000_000.00

        resultado = logica_pension.calcular_pension(datos)
        self.assertAlmostEqual(pension_esperada,resultado.pension,2)

    def test_excepcional_edad_limite_hombre(self):
        datos = logica_pension.DatosPension(
            ibc_ultimos_10=1_950_000,
            ibc_toda_vida=2_000_000,
            salario_minimo_legal=2_000_000,
            semanas_cotizadas=1300,
            edad=62,
            sexo="M"
        )

        pension_esperada = 2_000_000.00

        resultado = logica_pension.calcular_pension(datos)
        self.assertAlmostEqual(pension_esperada,resultado.pension,2)

    def test_excepcional_r_base_bajo_piso_55(self):
        datos = logica_pension.DatosPension(
            ibc_ultimos_10=32_000_000,
            ibc_toda_vida=32_500_000,
            salario_minimo_legal=2_000_000,
            semanas_cotizadas=1300,
            edad=65,
            sexo="M"
        )

        pension_esperada = 18_646_875.00

        resultado = logica_pension.calcular_pension(datos)

        self.assertAlmostEqual(pension_esperada,resultado.pension,2 )

    def test_excepcional_r_total_llega_tope_80(self):
        datos = logica_pension.DatosPension(
            ibc_ultimos_10=1_250_000,
            ibc_toda_vida=1_300_000,
            salario_minimo_legal=2_000_000,
            semanas_cotizadas=1800,
            edad=60,
            sexo="F"
        )

        pension_esperada = 2_000_000.00

        resultado = logica_pension.calcular_pension(datos)

        self.assertAlmostEqual( pension_esperada,resultado.pension,2 )

    def test_excepcional_49_semanas_no_alcanza_incremento(self):
        datos = logica_pension.DatosPension(
            ibc_ultimos_10=1_250_000,
            ibc_toda_vida=1_300_000,
            salario_minimo_legal=2_000_000,
            semanas_cotizadas=1349,
            edad=63,
            sexo="M"
        )

        pension_esperada = 2_000_000.00

        resultado = logica_pension.calcular_pension(datos)

        self.assertAlmostEqual(pension_esperada,resultado.pension, 2)


if __name__ == "__main__":
    unittest.main()
