import datetime
import os

import numpy as np
import pandas as pd

import matplotlib.colors
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.transforms as transforms
import matplotlib.ticker as ticker
import seaborn as sns
import src.utils as cutil

# save the figure here
save_fig = True
save_data = True

# in inches
fig_width = 3.5  # 89mm
fig_height = 6.7  # 249mm

# grid_width = 2.8  # 89mm
# grid_height = 7.5  # 249mm

grid_width = 2.5  # 89mm
grid_height = 6.7  # 249mm

scale_factor = 3.0 / 15.0  # old width was 15
scale_factor_x = 2.8 / 15.0  # old width was 15

leg_topright = True

fig_dir = cutil.HOME / "results" / "figures" / "fig4"
fig_data_dir = cutil.HOME / "results" / "source_data"
fig_data_fn = "Figure4_data.csv"


fig_dir.mkdir(parents=True, exist_ok=True)
fig_name = "fig4.pdf"

# for nice exporting to illustrator
matplotlib.rcParams["pdf.fonttype"] = 42

# figure aesthetics
no_policy_color = "#ED2224"
no_policy_uncertainty_color = "#F37F81"
# no_policy_color = "red"
policy_color = "#3A53A4"
policy_uncertainty_color = "#797CBB"
# policy_color = "blue"

matplotlib.rcParams["font.sans-serif"] = "Arial"
matplotlib.rcParams["font.family"] = "sans-serif"

# column indices for prediction data
pred_no_pol_key = "predicted_cum_confirmed_cases_no_policy"
pred_pol_key = "predicted_cum_confirmed_cases_true"

data_dir = cutil.MODELS / "projections"
fn_template = os.path.join(data_dir, "{0}_bootstrap_projection.csv")

countries_in_order = ["china", "korea", "italy", "iran", "france", "usa"]

country_names = {
    "france": "France",
    "iran": "Iran",
    "usa": "United States",
    "italy": "Italy",
    "china": "China",
    "korea": "South Korea",
}


country_abbrievations = {
    "france": "FRA",
    "iran": "IRN",
    "usa": "USA",
    "italy": "ITA",
    "china": "CHN",
    "korea": "KOR",
}


cutoff_dates = pd.read_csv(cutil.CODE / "data" / "cutoff_dates.csv").set_index("tag")
cutoff_end = str(cutoff_dates.loc["default", "end_date"])
end_date = "{0}-{1}-{2}".format(cutoff_end[0:4], cutoff_end[4:6], cutoff_end[6:8])
start_date = "2020-01-15"

# country specfic cutoff dates
cutoff_dates_by_country = {}
for country in countries_in_order:
    key_this_country = "{0}_analysis".format(country_abbrievations[country])

    if key_this_country in cutoff_dates.index:
        cutoff_this_country = str(cutoff_dates.loc[key_this_country, "end_date"])
        cutoff_dates_by_country[country] = "{0}-{1}-{2}".format(
            cutoff_this_country[0:4], cutoff_this_country[4:6], cutoff_this_country[6:8]
        )
    else:
        cutoff_dates_by_country[country] = end_date


def color_add_alpha(color, alpha):
    color_rgba = list(matplotlib.colors.to_rgba(color))
    color_rgba[3] = alpha
    return color_rgba


def plot_quantiles(ax, quantiles, quantiles_dict, legend_dict, model, update_legend):
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 10))

    dates = quantiles_dict["dates"]

    quantiles_no_policy = quantiles_dict["quantiles_no_policy"]
    quantiles_policy = quantiles_dict["quantiles_policy"]

    if model is not None:
        dates_model = pd.to_datetime(model["date"])
        preds_policy = model["predicted_cum_confirmed_cases_true"]
        preds_no_policy = model["predicted_cum_confirmed_cases_no_policy"]

    num_ranges = int(len(quantiles) / 2)

    upper_idx = -1
    lower_idx = 0

    # inner to outer - hardcode for now
    alphas_fc = [0.5, 1.0]

    if model is not None:
        model_no_pol = ax.plot(
            dates_model,
            preds_no_policy,
            color=no_policy_color,
            lw=5 * scale_factor,
            ls="--",
        )

        if update_legend:
            legend_dict["lines"].append(model_no_pol[0])

            if leg_topright:
                legend_dict["labels"].append('"No policy" \n scenario')
            else:
                egend_dict["labels"].append('"No policy" scenario')

    for i in range(num_ranges):
        if i >= 0:
            l_no_pol = ax.fill_between(
                pd.to_datetime(dates),
                quantiles_no_policy[:, lower_idx],
                quantiles_no_policy[:, upper_idx],
                facecolor=color_add_alpha(no_policy_uncertainty_color, alphas_fc[i]),
                #  edgecolor=color_add_alpha(no_policy_color, alphas_ec[i]),
                #   alpha = alphas_fc[i],
            )

            if update_legend:
                legend_dict["lines"].append(l_no_pol)
                legend_dict["labels"].append(
                    "{0}% interval".format(
                        int(100 * (quantiles[upper_idx] - quantiles[lower_idx]))
                    )
                )

        lower_idx += 1
        upper_idx -= 1

    if model is not None:
        model_pol = ax.plot(
            dates_model, preds_policy, color=policy_color, lw=5 * scale_factor, ls="--"
        )

        if update_legend:
            legend_dict["lines"].append(model_pol[0])

            if leg_topright:
                legend_dict["labels"].append("Actual policies \n (predicted)")
            else:
                legend_dict["labels"].append("Actual policies (predicted)")

    # reset
    upper_idx = -1
    lower_idx = 0

    for i in range(num_ranges):
        if i >= 0:
            l_pol = ax.fill_between(
                pd.to_datetime(dates),
                quantiles_policy[:, lower_idx],
                quantiles_policy[:, upper_idx],
                facecolor=color_add_alpha(policy_uncertainty_color, alphas_fc[i]),
                # edgecolor=color_add_alpha(policy_color, alphas_ec[i]),
            )

            if update_legend:
                legend_dict["lines"].append(l_pol)
                legend_dict["labels"].append(
                    "{0}% interval".format(
                        int(100 * (quantiles[upper_idx] - quantiles[lower_idx]))
                    )
                )

        lower_idx += 1
        upper_idx -= 1

    return ax


def plot_cases(ax, this_country_cases, legend_dict, update_legend):
    if ax is None:
        fig, ax = plt.subplots()

    dates_cases = pd.to_datetime(this_country_cases["date"])
    cases = this_country_cases["cases"].values

    case_scatter = ax.scatter(
        dates_cases.values,
        cases,
        marker="o",
        color="black",
        s=16 * scale_factor ** 2,
        clip_on=False,
    )
    if update_legend:
        legend_dict["lines"].append(case_scatter)

        if leg_topright:
            legend_dict["labels"].append("Cumulative \nobserved cases")
        else:
            legend_dict["labels"].append("Cumulative observed cases")

    return ax


def plot_model(ax, this_country_model, legend_dict, update_legend):
    if ax is None:
        fig, ax = plt.subplots()

    dates = pd.to_datetime(this_country_model["date"])
    preds_policy = this_country_model["predicted_cum_confirmed_cases_true"]
    preds_no_policy = this_country_model["predicted_cum_confirmed_cases_no_policy"]

    l_pol = ax.plot(dates, preds_policy, color=policy_color, lw=3, ls="--")

    l_no_pol = ax.plot(dates, preds_no_policy, color=no_policy_color, lw=3, ls="--")

    if update_legend:
        legend_dict["lines"].append(l_pol)
        legend_dict["lines"].append(l_no_pol)

        legend_dict["labels"].append("Prediction with policy")
        legend_dict["labels"].append("Prediction no policy")

    return ax


def make_quantiles(this_country_df, quantiles):
    df_by_date = this_country_df.groupby("date")
    quantiles_array_policy = np.zeros((len(df_by_date.groups.keys()), len(quantiles)))
    quantiles_array_no_policy = np.zeros(
        (len(df_by_date.groups.keys()), len(quantiles))
    )

    for d, date_idx in enumerate(df_by_date.groups.keys()):
        this_day = df_by_date.get_group(date_idx)

        for q, quantile in enumerate(quantiles):
            quantiles_array_policy[d, q] = np.quantile(
                this_day["predicted_cum_confirmed_cases_true"], quantile
            )
            quantiles_array_no_policy[d, q] = np.quantile(
                this_day["predicted_cum_confirmed_cases_no_policy"], quantile
            )

    dates = pd.to_datetime(list(df_by_date.groups.keys()))

    return dates, quantiles_array_policy, quantiles_array_no_policy


def plot_bracket(ax, model_df):
    # most recent case
    model_df["date"] = pd.to_datetime(model_df["date"])
    last_model_day = model_df["date"].max()

    start = (
        mdates.date2num(pd.to_datetime(last_model_day) + datetime.timedelta(days=1.5)),
        model_df.loc[model_df["date"] == last_model_day, pred_pol_key].values[0],
    )

    start_cap = (
        mdates.date2num(pd.to_datetime(last_model_day) + datetime.timedelta(days=1)),
        model_df.loc[model_df["date"] == last_model_day, pred_pol_key].values[0],
    )

    end = (
        mdates.date2num(pd.to_datetime(last_model_day) + datetime.timedelta(days=1.5)),
        model_df.loc[model_df["date"] == last_model_day, pred_no_pol_key].values[0],
    )

    end_cap = (
        mdates.date2num(pd.to_datetime(last_model_day) + datetime.timedelta(days=1)),
        model_df.loc[model_df["date"] == last_model_day, pred_no_pol_key].values[0],
    )

    # geometric mean is middle b/c log space
    text_spot_start = (
        mdates.date2num(pd.to_datetime(last_model_day) + datetime.timedelta(days=1.5)),
        np.sqrt(start[1] * end[1]),
    )
    text_spot_end = (
        mdates.date2num(pd.to_datetime(last_model_day) + datetime.timedelta(days=3)),
        np.sqrt(start[1] * end[1]),
    )

    # put line
    ax.arrow(
        start[0], start[1], 0, end[1] - start[1], lw=2 * scale_factor_x, clip_on=False
    )
    # put caps
    ax.arrow(
        start_cap[0],
        start_cap[1],
        start[0] - start_cap[0],
        0,
        lw=2 * scale_factor_x,
        clip_on=False,
    )
    ax.arrow(
        end_cap[0],
        end_cap[1],
        end[0] - end_cap[0],
        0,
        lw=2 * scale_factor_x,
        clip_on=False,
    )

    # rounds to the nearest 1,000
    # num_rounded = int(round(end[1] - start[1], -3))
    num_rounded = int(float("{0:.2}".format(end[1] - start[1])))
    annot = "~{0:,d} fewer\nestimated cases".format(num_rounded)
    # put text
    ax.annotate(
        annot,
        xy=text_spot_start,
        xytext=text_spot_end,
        annotation_clip=False,
        fontsize=27 * scale_factor_x,
        va="center",
    )


def annotate_cases(ax, cases):
    # get most recent case
    lastest_cases_date = cases["date"].max()

    cases_last = cases[cases["date"] == lastest_cases_date]["cases"].values[0]
    cases_date = pd.to_datetime(lastest_cases_date)

    cases_pos = (mdates.date2num(cases_date), cases_last)

    # divide for even spacing in log scale
    text_pos = (
        mdates.date2num(cases_date + datetime.timedelta(days=2)),
        cases_last / 100.0,
    )

    annot_date = cases_date.strftime("%b %-d")

    annot = "{0}: {1:,d} \nconfirmed cases".format(annot_date, int(cases_last))
    ax.annotate(
        annot,
        xy=cases_pos,
        xytext=text_pos,
        annotation_clip=False,
        fontsize=27 * scale_factor_x,
        va="center",
        arrowprops={
            "arrowstyle": "->",
            "shrinkA": 10 * scale_factor_x,
            "shrinkB": 10 * scale_factor_x,
            "connectionstyle": "arc3,rad=0.3",
            "color": "black",
            "lw": 1.5 * scale_factor_x,
        },
    )


def main():

    # initialize the dataframes that will get filled in
    dfs_by_country = [
        pd.DataFrame(
            {
                "country": country_names[c],
                "date": pd.date_range(start_date, end_date, freq="D"),
            }
        )
        for c in countries_in_order
    ]

    # read in all the cases data
    cases_dict = cutil.load_all_cases_deaths(cases_drop=True)

    # save that data
    for c, country in enumerate(countries_in_order):

        cases_df_this_country = cases_dict[country]

        dfs_by_country[c] = pd.merge(
            dfs_by_country[c].set_index("date", drop=False),
            cases_df_this_country.set_index("date"),
            left_index=True,
            right_index=True,
            how="left",
        )

    resampled_dfs_by_country = {}
    for country in countries_in_order:
        print("reading ", fn_template.format(country))
        resampled_dfs_by_country[country] = pd.read_csv(fn_template.format(country))

    # get central estimates
    model_dfs_by_country = {}
    for c, country in enumerate(countries_in_order):
        model_df_this_country = pd.read_csv(
            fn_template.replace("bootstrap", "model").format(country)
        )

        model_dfs_by_country[country] = model_df_this_country

        dfs_by_country[c] = pd.merge(
            dfs_by_country[c],
            model_df_this_country.set_index("date"),
            left_index=True,
            right_index=True,
            how="left",
        )

    # get quantile data
    quantiles = [0.025, 0.15, 0.85, 0.975]  # 95% range  # 70% range

    quantiles_by_country = {}
    for c, country in enumerate(countries_in_order):
        quantile_this_country = {}
        dates, quantiles_policy, quantiles_no_policy = make_quantiles(
            resampled_dfs_by_country[country], quantiles
        )

        quantile_this_country["dates"] = dates
        quantile_this_country["quantiles_policy"] = quantiles_policy
        quantile_this_country["quantiles_no_policy"] = quantiles_no_policy
        quantiles_by_country[country] = quantile_this_country

        # make a small df for this quantile so we can merge on date
        quantiles_this_country_dict = {}
        for q, quantile in enumerate(quantiles):
            key_start = "quantile_{0}_".format(quantile)
            quantiles_this_country_dict[key_start + "policy"] = quantiles_policy[:, q]
            quantiles_this_country_dict[key_start + "no_policy"] = quantiles_no_policy[
                :, q
            ]

        quantile_df = pd.DataFrame(
            quantiles_this_country_dict, index=pd.to_datetime(dates)
        )

        dfs_by_country[c] = pd.merge(
            dfs_by_country[c],
            quantile_df,
            how="left",
            left_index=True,
            right_index=True,
        )

    # plot
    fig, ax = plt.subplots(
        len(countries_in_order),
        figsize=(grid_width, grid_height),
        sharex=True,
        sharey=True,
    )

    legend_dict = {"lines": [], "labels": []}

    for c, country in enumerate(countries_in_order):
        # 1.a plot quantiles and model
        quantiles_this_country = quantiles_by_country[country]
        model_this_country = model_dfs_by_country[country]
        cases_this_country = cases_dict[country]

        # get the last date of cases and only display up until that date
        # last_cases_date_this_country = cases_this_country["date_str"].max()

        preds_before_last_cases_mask = model_this_country["date"].apply(
            lambda x: x <= cutoff_dates_by_country[country]
        )

        model_until_last_case = model_this_country.where(preds_before_last_cases_mask)

        quantiles_until_last_case = {}
        for quant_key, quant_array in quantiles_this_country.items():
            quantiles_until_last_case[quant_key] = quant_array[
                preds_before_last_cases_mask
            ]

        ax[c] = plot_quantiles(
            ax[c],
            quantiles,
            quantiles_until_last_case,
            legend_dict,
            model=model_until_last_case,
            update_legend=(c == 0),
        )

        # 1.b annotate the model on the right
        plot_bracket(ax[c], model_until_last_case)

        # 2.a plot cases where they overlap with predictions

        cases_overlap_preds_mask = cases_this_country["date_str"].apply(
            lambda x: x in model_this_country["date"].values
        )
        cases_overlapping_predictions = cases_this_country.where(
            cases_overlap_preds_mask
        )
        ax[c] = plot_cases(
            ax[c], cases_overlapping_predictions, legend_dict, update_legend=(c == 0)
        )

        # 2.b annotate cases
        annotate_cases(ax[c], cases_overlapping_predictions)

        # 3. set title and axis labels
        ax[c].set_title(
            " " + country_names[country],
            fontsize=35 * scale_factor,
            verticalalignment="top",
            loc="left",
            x=0.04,
            y=0.85,
            backgroundcolor="white",
            zorder=2,
            # pad=0.1,
        )

        ax[c].set_ylabel("Cumulative cases", fontsize=28 * scale_factor, labelpad=1)
        ax[c].set_yscale("log")

        ax[c].set_xlim(np.datetime64(start_date), np.datetime64(end_date))

        ax[c].set_ylim(10, 1e8)

        # dates on x axis
        days_all = mdates.DayLocator(interval=1)
        days_sparse = mdates.DayLocator(interval=10)
        formatter = mdates.DateFormatter("%b %-d")

        ax[c].xaxis.set_major_formatter(formatter)
        ax[c].xaxis.set_minor_locator(days_all)
        ax[c].xaxis.set_major_locator(days_sparse)

        # set to mostly match fig 3
        ax[c].tick_params(
            axis="x",
            which="major",
            labelsize=27 * scale_factor_x,
            length=10 * scale_factor_x,
            width=4 * scale_factor_x,
        )
        ax[c].tick_params(
            axis="x",
            which="minor",
            length=5 * scale_factor_x,
            width=1.5 * scale_factor_x,
        )

        # ax[c].set_yticks(ax[c].get_yticks(minor=True)[::5], minor=True)
        ax[c].set_yticks(np.logspace(1, 7, base=10, num=4))
        print(np.logspace(1, 7, base=10, num=4))
        ax[c].set_yticks(
            np.logspace(1, 8, base=10, num=8), minor=True,
        )
        print(np.logspace(1, 8, base=10, num=8))

        ax[c].tick_params(
            axis="y",
            which="major",
            labelsize=30 * scale_factor_x,
            length=8 * scale_factor,
            width=1 * scale_factor,
            zorder=10,
            pad=-0.2,
        )

        ax[c].tick_params(
            axis="y",
            which="minor",
            labelsize=27 * scale_factor_x,
            length=8 * scale_factor,
            width=1.5 * scale_factor,
            zorder=10,
        )

        ax[c].set_yticklabels([], minor=True)

        sns.despine(ax=ax[c], top=True)

        # thicken the axes
        plt.setp(ax[c].spines.values(), linewidth=2 * scale_factor)
        ax[c].grid(which="major", axis="x", lw=1 * scale_factor, zorder=1)
        ax[c].grid(which="minor", axis="y", lw=1 * scale_factor, zorder=1)

        ax[c].yaxis.offsetText.set_fontsize(24)

    # add another axis so the annotations don't go away
    # extra_ax = fig.add_axes([0, 0, 1.0, 1.0])
    # extra_ax.axis("off")

    if leg_topright:

        # add a legend axis
        leg_ax = fig.add_axes([0.88, 0.72, 0.1, 0.05])

        leg = leg_ax.legend(
            handles=legend_dict["lines"],
            labels=legend_dict["labels"],
            loc=(0.42, 0.2),
            fontsize=27 * scale_factor_x,
            title="Legend",
            frameon=False,
            markerscale=1.0 * scale_factor,
        )

    else:
        # add a legend axis
        leg_ax = fig.add_axes([0.1, 0.1, 0.1, 0.05])

        leg = leg_ax.legend(
            handles=legend_dict["lines"],
            labels=legend_dict["labels"],
            loc=(0.42, 1.2),
            fontsize=27 * scale_factor_x,
            title="Legend",
            frameon=True,
            markerscale=2 * scale_factor,
        )

    leg._legend_box.align = "left"
    plt.setp(leg.get_title(), fontsize=30 * scale_factor_x)

    leg_ax.axis("off")

    df_all_countries = pd.concat(dfs_by_country).drop(["date_str"], axis=1)

    if save_data:
        out_fn = fig_data_dir / fig_data_fn
        print("saving fig data in {0}".format(out_fn))
        # avoid rounding issues
        df_all_countries.to_csv(out_fn, index=False, float_format="%.3f")

    if save_fig:
        out_fn = fig_dir / fig_name
        print("saving fig in {0}".format(out_fn))
        # plt.savefig(out_fn, bbox_inches="tight", bbox_extra_artists=(leg,))
        vertical_pad_bottom = 0.56
        vertical_pad_top = 1.31
        horizontal_pad_left = 0.04
        horizontal_pad_right = 0.48
        plt.savefig(
            out_fn,
            bbox_inches=transforms.Bbox.from_bounds(
                horizontal_pad_left,
                0 + vertical_pad_bottom,
                fig_width - horizontal_pad_right,
                fig_height - (vertical_pad_top),
            ),
        )


if __name__ == "__main__":
    main()
