

class OrsesTokenMath:

    @staticmethod
    def convert_orses_tokens_to_ntakiris(amt: (str, float)) -> (int, None):

        try:

            ntakiri_amt = int(round(float(amt), 10) * 1e10)

        except ValueError as e:
            print(e)
            print(f"in OrsesTokenMath.py, convert_orses_tokens_to_ntakiris {amt} could not be converted into ntakiri amt")
            return None

        return ntakiri_amt


    @staticmethod
    def convert_ntakiris_to_orses_tokens(ntakiri_amt: int) -> (float, None):

        try:
            amt = round(ntakiri_amt/1e10, 10)
        except TypeError as e:
            print(e)
            print(f"in OrsesTokenMath.py, convert_ntakiris_to_orses_tokens {ntakiri_amt} "
                  f"could not be converted to orses token amounts")
            return None

        return amt

