"""
Aurora Data Extraction
Extract BQX and REG features from Aurora PostgreSQL
"""

import psycopg2
import pandas as pd
import yaml
from typing import Tuple, Optional
from datetime import datetime


class AuroraExtractor:
    """Extract BQX and REG features from Aurora database"""

    def __init__(self, config_path: str = "config/database.yaml"):
        """
        Initialize Aurora extractor

        Args:
            config_path: Path to database configuration file
        """
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        self.aurora_config = config['aurora']
        self.conn = None

    def connect(self):
        """Establish connection to Aurora"""
        self.conn = psycopg2.connect(
            host=self.aurora_config['host'],
            port=self.aurora_config['port'],
            database=self.aurora_config['database'],
            user=self.aurora_config['user'],
            password=self.aurora_config['password'],
            sslmode=self.aurora_config['sslmode']
        )

    def disconnect(self):
        """Close Aurora connection"""
        if self.conn:
            self.conn.close()

    def load_bqx(
        self,
        pair: str,
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        """
        Load BQX features for a pair

        Args:
            pair: Forex pair (e.g., 'eurusd')
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            DataFrame with BQX features
        """
        if not self.conn:
            self.connect()

        query = f"""
        SELECT
            ts_utc,
            rate,
            -- 15 min window
            w15_bqx_return, w15_bqx_max, w15_bqx_min,
            w15_bqx_avg, w15_bqx_stdev, w15_bqx_endpoint,
            -- 30 min window
            w30_bqx_return, w30_bqx_max, w30_bqx_min,
            w30_bqx_avg, w30_bqx_stdev, w30_bqx_endpoint,
            -- 45 min window
            w45_bqx_return, w45_bqx_max, w45_bqx_min,
            w45_bqx_avg, w45_bqx_stdev, w45_bqx_endpoint,
            -- 60 min window
            w60_bqx_return, w60_bqx_max, w60_bqx_min,
            w60_bqx_avg, w60_bqx_stdev, w60_bqx_endpoint,
            -- 75 min window
            w75_bqx_return, w75_bqx_max, w75_bqx_min,
            w75_bqx_avg, w75_bqx_stdev, w75_bqx_endpoint,
            -- Aggregates
            agg_bqx_return, agg_bqx_max, agg_bqx_min,
            agg_bqx_avg, agg_bqx_stdev, agg_bqx_range,
            agg_bqx_volatility
        FROM bqx.bqx_{pair}
        WHERE ts_utc >= %s AND ts_utc < %s
        ORDER BY ts_utc
        """

        df = pd.read_sql(
            query,
            self.conn,
            params=(start_date, end_date),
            parse_dates=['ts_utc']
        )

        df.set_index('ts_utc', inplace=True)
        return df

    def load_reg(
        self,
        pair: str,
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        """
        Load REG features for a pair

        Args:
            pair: Forex pair (e.g., 'eurusd')
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            DataFrame with REG features
        """
        if not self.conn:
            self.connect()

        query = f"""
        SELECT
            time as ts_utc,
            close as rate,
            -- Window features (60, 90, 150, 240, 390, 630)
            w60_slope, w60_intercept, w60_r2,
            w60_quad_a, w60_quad_b, w60_quad_c, w60_quad_norm,

            w90_slope, w90_intercept, w90_r2,
            w90_quad_a, w90_quad_b, w90_quad_c, w90_quad_norm,

            w150_slope, w150_intercept, w150_r2,
            w150_quad_a, w150_quad_b, w150_quad_c, w150_quad_norm,

            w240_slope, w240_intercept, w240_r2,
            w240_quad_a, w240_quad_b, w240_quad_c, w240_quad_norm,

            w390_slope, w390_intercept, w390_r2,
            w390_quad_a, w390_quad_b, w390_quad_c, w390_quad_norm,

            w630_slope, w630_intercept, w630_r2,
            w630_quad_a, w630_quad_b, w630_quad_c, w630_quad_norm
        FROM bqx.reg_{pair}
        WHERE time >= %s AND time < %s
        ORDER BY time
        """

        df = pd.read_sql(
            query,
            self.conn,
            params=(start_date, end_date),
            parse_dates=['ts_utc']
        )

        df.set_index('ts_utc', inplace=True)
        return df

    def load(
        self,
        pair: str,
        start_date: str,
        end_date: str
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Load both BQX and REG features

        Args:
            pair: Forex pair (e.g., 'eurusd')
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            Tuple of (bqx_df, reg_df)
        """
        bqx_df = self.load_bqx(pair, start_date, end_date)
        reg_df = self.load_reg(pair, start_date, end_date)

        return bqx_df, reg_df


if __name__ == "__main__":
    # Example usage
    extractor = AuroraExtractor()

    # Load EURUSD data for July 2024
    bqx, reg = extractor.load(
        pair='eurusd',
        start_date='2024-07-01',
        end_date='2024-08-01'
    )

    print(f"BQX shape: {bqx.shape}")
    print(f"REG shape: {reg.shape}")
    print(f"\nBQX columns: {bqx.columns.tolist()}")
    print(f"\nFirst BQX row:\n{bqx.head(1)}")

    extractor.disconnect()
