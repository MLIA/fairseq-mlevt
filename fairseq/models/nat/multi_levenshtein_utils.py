# Copyright (c) Facebook, Inc. and its affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import torch
from fairseq.utils import new_arange
from fairseq import libnat2


def pi_del(
    shape,
    y_tgt_star,
    pad_symbol=0,
    plh_symbol=0,
    bos_symbol=0,
    eos_symbol=0,
    Kmax=100,
    mode="binomial",
    device="cpu",
):
    """Operations and states to edit a partially deleted version of y_star back to y_star."""
    # shape = B x N x M    ou B x L
    # y_tgt_star : B x M   ou B x L
    # if len(shape) == 2:
    #     # shape = list(shape)
    #     # shape[-1] = y_tgt_star.size(-1)
    #     # shape = tuple(shape)

    #     del_tgt = torch.ones(shape, dtype=torch.long, device=device)
    #     plh_tgt = -torch.ones(
    #         (shape[0], shape[1] - N), dtype=torch.long, device=device
    #     )
    #     cmb_tgt = -torch.ones(shape[0], shape[1], dtype=torch.long, device=device)

    #     y_plh = torch.full(
    #         (shape[0], shape[1]), pad_symbol, dtype=torch.long, device=device
    #     )
    #     y_cmb = torch.full(shape, pad_symbol, dtype=torch.long, device=device)
    #     y_tok = torch.full_like(y_tgt_star, pad_symbol, dtype=torch.long, device=device)

    #     # y_star_n = y_tgt_star.view(shape[0], 1, shape[-1]).expand(shape)
    #     y_star_n = torch.cat([y_tgt_star]*3, -1)

    #     # tok_mask = torch.zeros_like(y_star_n, dtype=bool, device=device)
    #     if mode == "uniform":
    #         raise NotImplementedError(f"{mode} not implemented")
    #         ...
    #     else:
    #         # what we keep
    #         mask = (
    #             ((torch.rand(y_star_n.shape, device=device) > 0.2) & (y_star_n.ne(pad_symbol)))
    #             | (y_star_n == bos_symbol)
    #             | (y_star_n == eos_symbol)
    #         )
        
    #     sorted_ = mask.long().sort(stable=True, descending=True, dim=-1)
    #     sorted_mask = sorted_[0].bool()
    #     y_plh[sorted_mask] = y_star_n[mask]
    #     y_cmb[y_star_n.ne(pad_symbol)] = plh_symbol
    #     y_cmb[mask] = y_star_n[mask]
    #     y_tok[y_tgt_star.ne(pad_symbol)] = plh_symbol

    #     tok_mask = mask.any(1) # if any seq_i kept
    #     y_tok[tok_mask] = y_tgt_star[tok_mask]

    #     idx = sorted_[1]

    #     plh_tgt = idx[:, :, 1:] - idx[:, :, :-1] - 1
    #     plh_tgt[~sorted_mask[:, :, 1:]] = 0
    #     plh_tgt = plh_tgt.clamp(0, Kmax - 1)

    #     cmb_tgt = mask.long()

    #     plh_mask = y_plh.ne(pad_symbol)[:, :, 1:]
    #     del_mask = torch.zeros(shape, dtype=bool, device=device)
    #     cmb_mask = y_tgt_star.ne(pad_symbol).view(shape[0], 1, shape[-1]).expand_as(y_cmb)
    # else:
    shape = list(shape)
    shape[-1] = y_tgt_star.size(-1)
    shape = tuple(shape)

    del_tgt = torch.ones(shape, dtype=torch.long, device=device)
    plh_tgt = -torch.ones(
        (shape[0], shape[1], shape[2] - 1), dtype=torch.long, device=device
    )
    cmb_tgt = -torch.ones(shape[0], shape[2], shape[1], dtype=torch.long, device=device)

    y_plh = torch.full(
        (shape[0], shape[1], shape[2]), pad_symbol, dtype=torch.long, device=device
    )
    y_cmb = torch.full(shape, pad_symbol, dtype=torch.long, device=device)
    y_tok = torch.full_like(y_tgt_star, pad_symbol, dtype=torch.long, device=device)

    y_star_n = y_tgt_star.view(shape[0], 1, shape[-1]).expand(shape)

    # tok_mask = torch.zeros_like(y_star_n, dtype=bool, device=device)
    if mode == "uniform":
        raise NotImplementedError(f"{mode} not implemented")
        ...
    else:
        mask = (
            ((torch.rand(y_star_n.shape, device=device) > 0.2) & (y_star_n.ne(pad_symbol)))
            | (y_star_n == bos_symbol)
            | (y_star_n == eos_symbol)
        )

    tok_mask = mask.any(1)
    sorted_ = mask.long().sort(stable=True, descending=True, dim=-1)
    sorted_mask = sorted_[0].bool()
    y_plh[sorted_mask] = y_star_n[mask]
    y_cmb[y_star_n.ne(pad_symbol)] = plh_symbol
    y_cmb[mask] = y_star_n[mask]
    y_tok[y_tgt_star.ne(pad_symbol)] = plh_symbol
    y_tok[tok_mask] = y_tgt_star[tok_mask]

    idx = sorted_[1]

    plh_tgt = idx[:, :, 1:] - idx[:, :, :-1] - 1
    plh_tgt[~sorted_mask[:, :, 1:]] = 0
    plh_tgt = plh_tgt.clamp(0, Kmax - 1)

    cmb_tgt = mask.long()

    plh_mask = y_plh.ne(pad_symbol)[:, :, 1:]
    del_mask = torch.zeros(shape, dtype=bool, device=device)
    cmb_mask = y_tgt_star.ne(pad_symbol).view(shape[0], 1, shape[-1]).expand_as(y_cmb)

    return {
        "del_tgt": del_tgt,
        "plh_tgt": plh_tgt,
        "cmb_tgt": cmb_tgt,
        "tok_tgt": y_tgt_star,
        "del_mask": del_mask,
        "plh_mask": plh_mask,
        "cmb_mask": cmb_mask,
        "tok_mask": tok_mask,
        "y_plh": y_plh,
        "y_cmb": y_cmb,
        "y_tok": y_tok,
    }


def pi_del_single(
    # input_len,
    y_tgt_star,
    pad_symbol=0,
    plh_symbol=0,
    bos_symbol=0,
    eos_symbol=0,
    Kmax=100,
    mode="uniform_length",
    device="cpu",
):
    """Operations and states to edit a partially deleted version of y_star back to y_star."""
    # y_tgt_star : B x M
    shape = list(y_tgt_star.shape)
    # shape[1] = input_len

    plh_tgt = -torch.ones(
        (shape[0], shape[1] - 1), dtype=torch.long, device=device
    )
    y_plh = torch.full(
        (shape[0], shape[1]), pad_symbol, dtype=torch.long, device=device
    )

    if mode == "uniform_length":
        tgt_mask = y_tgt_star.eq(pad_symbol)
        lengths = y_tgt_star.ne(pad_symbol).sum(-1)
        score_select = y_tgt_star.clone().float().uniform_()
        score_select.masked_fill_(
            y_tgt_star.eq(eos_symbol) | y_tgt_star.eq(bos_symbol),
            0.
        )
        score_select.masked_fill_(
            tgt_mask,
            1.
        )
        cutoff = 2 + ((lengths - 2).unsqueeze(1) * score_select.new_zeros(y_tgt_star.size(0), 1).uniform_()).long()
        # print("cutoff", cutoff, "/", lengths)
        # print("select", score_select)
        # print("sorted select", score_select.sort(1)[1])
        mask_index = torch.arange(shape[1], dtype=torch.long, device=device)[None, :].expand_as(y_tgt_star) < cutoff
        indexes = score_select.sort(dim=1, stable=True)[1]
        indexes[~mask_index] = 0
        mask = torch.zeros_like(tgt_mask)
        # print(indexes)
        batch_index = torch.arange(shape[0], dtype=torch.long, device=device)[:, None].expand_as(y_tgt_star)
        mask[batch_index, indexes] = True
        # mask = score_select.sort(dim=1, stable=True)[1] < cutoff
        # print("mask", mask)
        
        # print(mask.long())
    else:
        # mask of what is kept
        mask = (
            ((torch.rand(y_tgt_star.shape, device=device) > 0.2) & (y_tgt_star.ne(pad_symbol)))
            | (y_tgt_star == bos_symbol)
            | (y_tgt_star == eos_symbol)
        )

    sorted_ = mask.long().sort(stable=True, descending=True, dim=-1)
    sorted_mask = sorted_[0].bool()
    # print(y_plh.shape, sorted_mask.shape, y_tgt_star.shape, mask.shape)
    y_plh[sorted_mask] = y_tgt_star[mask]

    idx = sorted_[1]

    plh_tgt = idx[:, 1:] - idx[:, :-1] - 1
    plh_tgt[~sorted_mask[:, 1:]] = 0
    plh_tgt = plh_tgt.clamp(0, Kmax - 1)

    plh_mask = y_plh.ne(pad_symbol)[:, 1:]


    return {
        "plh_tgt": plh_tgt,
        "plh_mask": plh_mask,
        "y_plh": y_plh,
    }


def pi_sel(
    y_cmb_star,
    y_refs,
    gamma,
    pad_symbol=None,
    plh_symbol=None,
    bos_symbol=None,
    eos_symbol=None,
    device="cuda:0",
):
    """Replace some <plh> by tokens from y_refs (usually the tokens to edit)."""
    # y_cmb_star : B x N x M
    # y_refs : B x N x M

    assert y_cmb_star.shape == y_refs.shape, str(y_cmb_star.shape) + str(y_refs.shape)
    assert ((y_cmb_star == eos_symbol).sum(-1) == 1).all().item(), ((y_cmb_star == bos_symbol).sum(-1) == 1).all().item()

    mask = (y_cmb_star == plh_symbol) * (
        torch.rand(y_cmb_star.shape, device=device) < gamma
    )
    y_cmb = y_cmb_star.clone()
    mask_ref_sel = y_refs.ne(pad_symbol) & y_refs.ne(bos_symbol) & y_refs.ne(eos_symbol)
    dividend = mask_ref_sel.sum(-1).unsqueeze(-1).expand(y_refs.shape)  # B x N x M
    mask_void = (dividend[:, :, 0].ne(0).all(-1))
    idxs = new_arange(y_refs[mask_void])

    idxs = torch.remainder(idxs, dividend[mask_void]) + 1
    idxs = idxs[:, :, torch.randperm(idxs.size(-1))]
    mask[~mask_void] = False

    y_cmb[mask] = torch.gather(y_refs[mask_void], 2, idxs)[mask[mask_void]]

    return y_cmb


def pi_mask(
    y_star,
    pad_symbol=None,
    plh_symbol=None,
    bos_symbol=None,
    eos_symbol=None,
    device="cuda:0",
):
    """Mask some tokens with <plh> from the target sequence and learn to predict correct tokens."""
    y_tok = y_star.clone()

    y_tok[
        (torch.rand(y_tok.shape, device=device) > 0.7)
        * (y_tok.ne(pad_symbol))
        * y_tok.ne(bos_symbol)
        * y_tok.ne(eos_symbol)
    ] = plh_symbol
    tok_mask = y_tok == plh_symbol
    tok_tgt = y_star

    return y_tok, tok_tgt, tok_mask


def pi_star(
    y_del, y_star, k=10, max_valency=-1, pad_symbol=None, plh_symbol=None, Kmax=100, device="cuda:0"
):
    """Quasi optimal operations and states to edit y_del to y_star"""
    # y_del : B x N x M
    # y_star : B x M
    if y_del.size(1) == 1:
        k = 1
    ops = libnat2.MultiLevEditOps(y_del.cpu(), y_star.cpu(), k, max_valency, pad_symbol, plh_symbol)

    cmb_tgt = ops.get_cmb().to(device)
    y_tok = ops.get_s_cmb().to(device)
    

    return {
        "del_tgt": ops.get_del().to(device),
        "plh_tgt": ops.get_ins().clamp(0, Kmax - 1).to(device),
        "cmb_tgt": cmb_tgt,
        "tok_tgt": y_star,
        "del_mask": y_del.ne(pad_symbol),
        "plh_mask": ops.get_s_del().ne(pad_symbol).to(device)[:, :, 1:],
        "cmb_mask": y_star.ne(pad_symbol)
            .view(y_star.size(0), 1, y_star.size(1))
            .expand_as(ops.get_s_ins()),
        "tok_mask": (ops.get_s_cmb().to(device) == plh_symbol),
        "y_plh": ops.get_s_del().to(device),
        "y_cmb": ops.get_s_ins().to(device),
        "y_tok": y_tok,
    }


def handle_all_plh_case(cmb_tgt, y_tok, y_cmb, plh_symbol):
    msk_cmb_sel = ((y_tok == plh_symbol) & ((y_cmb == plh_symbol).all(1))).unsqueeze(1).expand_as(cmb_tgt) & (y_cmb == plh_symbol)
    cmb_tgt[msk_cmb_sel] = 1
    return cmb_tgt


def apply_del(in_tokens, in_scores, in_attn, word_del_pred, padding_idx, bos_idx, eos_idx):
    # word_del_pred: B x N x M in {False, True}
    # apply deletion to a tensor
    in_masks = in_tokens.ne(padding_idx)
    bos_eos_masks = in_tokens.eq(bos_idx) | in_tokens.eq(eos_idx)

    max_len = in_tokens.size(2)
    word_del_pred = word_del_pred.bool()
    word_del_pred = ~word_del_pred
    word_del_pred.masked_fill_(~in_masks, 1)
    word_del_pred.masked_fill_(bos_eos_masks, 0)  # do not delete bos/eos

    reordering = new_arange(in_tokens).masked_fill_(word_del_pred, max_len).sort(2)[1]

    out_tokens = in_tokens.masked_fill(word_del_pred, padding_idx).gather(2, reordering)

    out_scores = None
    if in_scores is not None:
        out_scores = in_scores.masked_fill(word_del_pred, 0).gather(2, reordering)

    out_attn = None
    if in_attn is not None:
        _mask = word_del_pred[:, :, :, None].expand_as(in_attn)
        _reordering = reordering[:, :, :, None].expand_as(in_attn)
        out_attn = in_attn.masked_fill(_mask, 0.0).gather(2, _reordering)

    return out_tokens, out_scores, out_attn


def apply_plh(in_tokens, in_scores, plh_pred, padding_idx, unk_idx, eos_idx):
    # plh_pred: B x N x M in {0, 1, ..., K_max - 1}
    # print("in tokens shape =", in_tokens.shape)
    # print("plh_pred shape  =", plh_pred.shape )
    in_masks = in_tokens.ne(padding_idx)
    in_lengths = in_masks.sum(2)
    # print("in toks", in_tokens[1].squeeze().cpu().numpy())
    # print("plh pred", plh_pred[1].squeeze().cpu().numpy())

    # HACK: hacky way to shift all the paddings to eos first.
    in_tokens.masked_fill_(~in_masks, eos_idx)
    plh_pred.masked_fill_(~in_masks[:, :, 1:], 0)

    out_lengths = in_lengths + plh_pred.sum(2)  # B x N
    # print("out_lengths", out_lengths.squeeze().cpu().numpy())
    out_masks = (
        new_arange(out_lengths, out_lengths.max())[None, :] < out_lengths[:, :, None]
    )
    # print("out_masks", out_masks.squeeze().cpu().numpy())

    reordering = (plh_pred + in_masks[:, :, 1:].long()).cumsum(2)
    # print("reordering", reordering.squeeze().cpu().numpy())
    out_tokens = (
        in_tokens.new_zeros(in_tokens.size(0), in_tokens.size(1), out_lengths.max())
        .fill_(padding_idx)
        .masked_fill_(out_masks, unk_idx)
    )
    out_tokens[:, :, 0] = in_tokens[:, :, 0]
    # print(out_tokens[:, :, 1:].shape, reordering.shape, in_tokens[:, :, 1:].shape)
    # print(reordering.max(), out_lengths.max())
    out_tokens[:, :, :].scatter_(2, reordering, in_tokens[:, :, 1:])

    out_scores = None
    if in_scores is not None:
        in_scores.masked_fill_(~in_masks, 0)
        out_scores = in_scores.new_zeros(*out_tokens.size())
        out_scores[:, :, 0] = in_scores[:, :, 0]
        out_scores.scatter_(2, reordering, in_scores[:, :, 1:])

    # print("out toks", out_tokens[1].squeeze().cpu().numpy())

    return out_tokens, out_scores


def apply_cmb(in_tokens, in_scores, cmb_pred, padding_idx, bos_idx, eos_idx, unk_idx):
    # combine choice
    # cmb_pred: B x M x N in [0, 1] (float!)
    # in_tokens: B x N x M
    cmb_pred = cmb_pred.max(-1)[1]
    in_masks = in_tokens.ne(padding_idx)
    in_cmb_lengths = (in_masks.sum(1) > 0).sum(-1)  # B

    out_tokens = torch.full(
        (in_tokens.size(0), in_tokens.size(2)), padding_idx, device=in_tokens.device
    )
    out_masks = (
        new_arange(in_cmb_lengths, in_tokens.size(-1))[None, :]
        < in_cmb_lengths[:, None]
    )
    #    out_tokens[out_masks] = unk_idx

    idx1 = (
        new_arange(in_cmb_lengths, in_tokens.size(0))
        .expand(in_tokens.size(2), in_tokens.size(0))
        .t()
    )
    idx2 = new_arange(in_cmb_lengths, in_tokens.size(2)).expand(
        in_tokens.size(0), in_tokens.size(2)
    )

    chosen = in_tokens.transpose(1, 2)[idx1, idx2, cmb_pred]

    out_tokens[out_masks] = chosen[out_masks]

    out_scores = None
    if in_scores is not None:
        out_scores = torch.full(
            (in_tokens.size(0), in_tokens.size(2)),
            0.,
            device=in_tokens.device,
            dtype=in_scores.dtype
        )
        chosen_score = in_scores.transpose(1, 2)[idx1, idx2, cmb_pred]
        out_scores[out_masks] = chosen_score[out_masks]

    return out_tokens, out_scores


def apply_tok(in_tokens, in_scores, tok_pred, tok_scores, unk_idx):
    tok_masks = in_tokens.eq(unk_idx)
    out_tokens = in_tokens.masked_scatter(tok_masks, tok_pred[tok_masks])

    if in_scores is not None:
        out_scores = in_scores.masked_scatter(
            tok_masks, tok_scores[tok_masks]
        )
    else:
        out_scores = None

    return out_tokens, out_scores


def _skip(x, mask):
    """
    Getting sliced (dim=0) tensor by mask. Supporting tensor and list/dict of tensors.
    """
    if isinstance(x, int):
        return x

    if x is None:
        return None

    if isinstance(x, torch.Tensor):
        if x.size(0) == mask.size(0):
            return x[mask]
        elif x.size(1) == mask.size(0):
            return x[:, mask]

    if isinstance(x, list):
        return [_skip(x_i, mask) for x_i in x]

    if isinstance(x, dict):
        return {k: _skip(v, mask) for k, v in x.items()}

    raise NotImplementedError


def _skip_encoder_out(encoder, encoder_out, mask):
    if not mask.any():
        return encoder_out
    else:
        return encoder.reorder_encoder_out(
            encoder_out, mask.nonzero(as_tuple=False).squeeze()
        )


def _fill(x, mask, y, padding_idx):
    """
    Filling tensor x with y at masked positions (dim=0).
    """
    if x is None:
        return y
    assert x.dim() == y.dim() and mask.size(0) == x.size(0)
    assert x.dim() == 2 or x.dim() == 3 or (x.dim() == 4 and x.size(3) == y.size(3))
    n_selected = mask.sum()
    assert n_selected == y.size(0)

    if n_selected == x.size(0):
        return y

    if x.size(1) < y.size(1):
        dims = [x.size(0), y.size(1) - x.size(1)]
        if x.dim() == 3:
            dims.append(x.size(2))
        x = torch.cat([x, x.new_zeros(*dims).fill_(padding_idx)], 1)
        x[mask] = y
    elif x.size(1) > y.size(1):
        x[mask] = padding_idx
        if x.dim() == 2:
            x[mask, : y.size(1)] = y
        elif x.dim() == 3:
            x[mask, : y.size(1), :] = y
        else:
            x[mask, : y.size(1), :, :] = y
    elif x.dim() == 3 and (x.size(2) < y.size(2)):
        dims = [x.size(0), x.size(1), y.size(2) - x.size(2)]
        x = torch.cat([x, x.new_zeros(*dims).fill_(padding_idx)], 2)
        x[mask] = y
    elif x.dim() == 3 and (x.size(2) > y.size(2)):
        x[mask] = padding_idx
        x[mask, :, :y.size(2)] = y
        # raise NotImplementedError("not implemented by myself")
    else:
        x[mask] = y
    return x
